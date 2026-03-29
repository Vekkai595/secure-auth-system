from datetime import datetime, timedelta, timezone

from app.core.security import verify_password
from app.core.tokens import create_password_reset_token
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.password_reset_repository import PasswordResetRepository


def register(client, email='user@example.com', username='user1', password='StrongPassword123'):
    return client.post('/api/v1/auth/register', json={'email': email, 'username': username, 'password': password})


def login(client, identifier='user@example.com', password='StrongPassword123', device='device-a'):
    return client.post('/api/v1/auth/login', json={'identifier': identifier, 'password': password}, headers={'X-Device-ID': device})


def auth_header(token: str):
    return {'Authorization': f'Bearer {token}'}


def test_health(client):
    res = client.get('/api/v1/health')
    assert res.status_code == 200
    assert res.json()['status'] == 'ok'


def test_register_success(client):
    res = register(client)
    assert res.status_code == 201


def test_register_duplicate_email(client):
    register(client)
    res = register(client, username='other')
    assert res.status_code == 400
    assert res.json()['error'] == 'user_already_exists'


def test_register_duplicate_username(client):
    register(client)
    res = register(client, email='other@example.com')
    assert res.status_code == 400


def test_register_invalid_username(client):
    res = client.post('/api/v1/auth/register', json={'email': 'a@a.com', 'username': 'bad space', 'password': 'StrongPassword123'})
    assert res.status_code == 422


def test_login_success(client):
    register(client)
    res = login(client)
    assert res.status_code == 200
    data = res.json()
    assert data['access_token']
    assert data['refresh_token']


def test_login_with_username_success(client):
    register(client)
    res = login(client, identifier='user1')
    assert res.status_code == 200


def test_login_invalid_password(client):
    register(client)
    res = login(client, password='WrongPassword999')
    assert res.status_code == 401
    assert res.json()['error'] == 'invalid_credentials'


def test_rate_limit_after_repeated_invalid_logins(client):
    register(client)
    for _ in range(5):
        res = login(client, password='WrongPassword999')
        assert res.status_code == 401
    res = login(client, password='WrongPassword999')
    assert res.status_code == 429
    assert res.json()['error'] == 'rate_limited'


def test_me_endpoint(client):
    register(client)
    tokens = login(client).json()
    res = client.get('/api/v1/users/me', headers=auth_header(tokens['access_token']))
    assert res.status_code == 200
    assert res.json()['email'] == 'user@example.com'


def test_invalid_access_token_returns_401(client):
    res = client.get('/api/v1/users/me', headers=auth_header('invalid.token.here'))
    assert res.status_code == 401
    assert res.json()['error'] == 'invalid_token'


def test_refresh_success(client):
    register(client)
    tokens = login(client).json()
    res = client.post('/api/v1/auth/refresh', json={'refresh_token': tokens['refresh_token']}, headers={'X-Device-ID': 'device-a'})
    assert res.status_code == 200
    assert res.json()['refresh_token'] != tokens['refresh_token']


def test_refresh_invalid_token(client):
    register(client)
    res = client.post('/api/v1/auth/refresh', json={'refresh_token': 'bad-token'}, headers={'X-Device-ID': 'device-a'})
    assert res.status_code == 401


def test_refresh_expired_token(client, db_session):
    register(client)
    tokens = login(client).json()
    db = db_session()
    token = db.query(RefreshToken).first()
    token.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()
    db.close()
    res = client.post('/api/v1/auth/refresh', json={'refresh_token': tokens['refresh_token']}, headers={'X-Device-ID': 'device-a'})
    assert res.status_code == 401


def test_logout_success(client):
    register(client)
    tokens = login(client).json()
    res = client.post('/api/v1/auth/logout', json={'refresh_token': tokens['refresh_token']}, headers=auth_header(tokens['access_token']))
    assert res.status_code == 200


def test_logout_wrong_owner_denied(client):
    register(client)
    tokens1 = login(client).json()
    register(client, email='two@example.com', username='two', password='StrongPassword123')
    tokens2 = login(client, identifier='two@example.com', device='device-b').json()
    res = client.post('/api/v1/auth/logout', json={'refresh_token': tokens1['refresh_token']}, headers=auth_header(tokens2['access_token']))
    assert res.status_code == 401


def test_logout_all_revokes_sessions(client):
    register(client)
    t1 = login(client, device='device-a').json()
    login(client, device='device-b')
    res = client.post('/api/v1/auth/logout-all', headers=auth_header(t1['access_token']))
    assert res.status_code == 200
    sessions = client.get('/api/v1/sessions', headers=auth_header(t1['access_token']))
    assert sessions.status_code == 200
    assert all(item['revoked_at'] is not None for item in sessions.json()['items'])


def test_session_list_and_revoke(client):
    register(client)
    tokens = login(client).json()
    sessions = client.get('/api/v1/sessions', headers=auth_header(tokens['access_token']))
    assert sessions.status_code == 200
    session_id = sessions.json()['items'][0]['id']
    revoke = client.delete(f'/api/v1/sessions/{session_id}', headers=auth_header(tokens['access_token']))
    assert revoke.status_code == 200


def test_revoke_session_wrong_owner(client):
    register(client)
    t1 = login(client).json()
    session_id = client.get('/api/v1/sessions', headers=auth_header(t1['access_token'])).json()['items'][0]['id']
    register(client, email='two@example.com', username='two', password='StrongPassword123')
    t2 = login(client, identifier='two@example.com', device='device-b').json()
    res = client.delete(f'/api/v1/sessions/{session_id}', headers=auth_header(t2['access_token']))
    assert res.status_code == 400


def test_last_seen_updates_on_authenticated_request(client):
    register(client)
    tokens = login(client).json()
    before = client.get('/api/v1/sessions', headers=auth_header(tokens['access_token'])).json()['items'][0]['last_seen_at']
    client.get('/api/v1/users/me', headers=auth_header(tokens['access_token']))
    after = client.get('/api/v1/sessions', headers=auth_header(tokens['access_token'])).json()['items'][0]['last_seen_at']
    assert after >= before


def test_same_device_refresh_keeps_single_session(client):
    register(client)
    tokens = login(client, device='stable-device').json()
    client.post('/api/v1/auth/refresh', json={'refresh_token': tokens['refresh_token']}, headers={'X-Device-ID': 'stable-device'})
    sessions = client.get('/api/v1/sessions', headers=auth_header(tokens['access_token']))
    assert len(sessions.json()['items']) == 1


def test_two_devices_create_two_sessions(client):
    register(client)
    t1 = login(client, device='device-a').json()
    login(client, device='device-b')
    sessions = client.get('/api/v1/sessions', headers=auth_header(t1['access_token']))
    assert len(sessions.json()['items']) == 2


def test_forgot_password_generic_message(client):
    register(client)
    res = client.post('/api/v1/auth/forgot-password', json={'email': 'user@example.com'})
    assert res.status_code == 200
    assert 'reset token' not in res.json()['message'].lower()


def test_password_reset_success(client, db_session):
    register(client)
    db = db_session()
    user = db.query(User).filter_by(email='user@example.com').first()
    token, expires_at = create_password_reset_token(user.id)
    PasswordResetRepository(db).create(user_id=user.id, token_hash=__import__('hashlib').sha256(token.encode()).hexdigest(), expires_at=expires_at)
    db.commit()
    db.close()
    res = client.post('/api/v1/auth/reset-password', json={'reset_token': token, 'new_password': 'EvenStronger123'})
    assert res.status_code == 200
    db = db_session()
    user = db.query(User).filter_by(email='user@example.com').first()
    assert verify_password('EvenStronger123', user.password_hash)
    db.close()


def test_password_reset_invalid_token(client):
    register(client)
    res = client.post('/api/v1/auth/reset-password', json={'reset_token': 'bad', 'new_password': 'EvenStronger123'})
    assert res.status_code == 401


def test_password_reset_expired_token(client, db_session):
    register(client)
    db = db_session()
    user = db.query(User).filter_by(email='user@example.com').first()
    token, _ = create_password_reset_token(user.id)
    PasswordResetRepository(db).create(user_id=user.id, token_hash=__import__('hashlib').sha256(token.encode()).hexdigest(), expires_at=datetime.now(timezone.utc) - timedelta(minutes=1))
    db.commit()
    db.close()
    res = client.post('/api/v1/auth/reset-password', json={'reset_token': token, 'new_password': 'EvenStronger123'})
    assert res.status_code == 401


def test_missing_bearer_token(client):
    res = client.get('/api/v1/users/me')
    assert res.status_code == 401


def test_request_id_present_on_error(client):
    res = client.get('/api/v1/users/me', headers=auth_header('bad.token'))
    assert res.status_code == 401
    assert res.json()['request_id']
