import json
import pytest
from unittest.mock import patch, MagicMock
from src.api import users


@pytest.fixture
def mock_dynamodb_table():
    with patch('src.api.users.get_table') as mock_get_table:
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        yield mock_table


def test_get_all_users(mock_dynamodb_table):
    mock_dynamodb_table.scan.return_value = {
        'Items': [
            {'userid': '123', 'name': 'John'},
            {'userid': '456', 'name': 'Jane'}
        ]
    }
    
    event = {
        'httpMethod': 'GET',
        'resource': '/users'
    }
    
    response = users.lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert len(body) == 2
    assert body[0]['userid'] == '123'
    mock_dynamodb_table.scan.assert_called_once()


def test_get_user_by_id_found(mock_dynamodb_table):
    mock_dynamodb_table.get_item.return_value = {
        'Item': {'userid': '123', 'name': 'John'}
    }
    
    event = {
        'httpMethod': 'GET',
        'resource': '/users/{userid}',
        'pathParameters': {'userid': '123'}
    }
    
    response = users.lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['userid'] == '123'
    assert body['name'] == 'John'


def test_get_user_by_id_not_found(mock_dynamodb_table):
    mock_dynamodb_table.get_item.return_value = {}
    
    event = {
        'httpMethod': 'GET',
        'resource': '/users/{userid}',
        'pathParameters': {'userid': '999'}
    }
    
    response = users.lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body == {}


def test_create_user_with_id(mock_dynamodb_table):
    event = {
        'httpMethod': 'PUT',
        'resource': '/users',
        'body': json.dumps({'userid': '123', 'name': 'John'})
    }
    
    response = users.lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['userid'] == '123'
    assert body['name'] == 'John'
    assert 'timestamp' in body
    mock_dynamodb_table.put_item.assert_called_once()


def test_create_user_without_id(mock_dynamodb_table):
    event = {
        'httpMethod': 'PUT',
        'resource': '/users',
        'body': json.dumps({'name': 'John'})
    }
    
    response = users.lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert 'userid' in body
    assert body['name'] == 'John'
    assert 'timestamp' in body


def test_update_user(mock_dynamodb_table):
    event = {
        'httpMethod': 'PUT',
        'resource': '/users/{userid}',
        'pathParameters': {'userid': '123'},
        'body': json.dumps({'name': 'John Updated'})
    }
    
    response = users.lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['userid'] == '123'
    assert body['name'] == 'John Updated'
    assert 'timestamp' in body


def test_delete_user(mock_dynamodb_table):
    event = {
        'httpMethod': 'DELETE',
        'resource': '/users/{userid}',
        'pathParameters': {'userid': '123'}
    }
    
    response = users.lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body == {}
    mock_dynamodb_table.delete_item.assert_called_once_with(
        Key={'userid': '123'}
    )


def test_unsupported_route(mock_dynamodb_table):
    event = {
        'httpMethod': 'POST',
        'resource': '/invalid'
    }
    
    response = users.lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['Message'] == 'Unsupported route'


def test_error_handling(mock_dynamodb_table):
    mock_dynamodb_table.scan.side_effect = Exception('DynamoDB error')
    
    event = {
        'httpMethod': 'GET',
        'resource': '/users'
    }
    
    response = users.lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'Error:' in body


def test_response_headers(mock_dynamodb_table):
    mock_dynamodb_table.scan.return_value = {'Items': []}
    
    event = {
        'httpMethod': 'GET',
        'resource': '/users'
    }
    
    response = users.lambda_handler(event, None)
    
    assert response['headers']['Content-Type'] == 'application/json'
    assert response['headers']['Access-Control-Allow-Origin'] == '*'
