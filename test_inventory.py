
import pytest
from unittest.mock import patch, MagicMock
import requests
from App.main import app as flask_app
import cli_tool as cli_tool


# FIXTURES

@pytest.fixture
def client():
    """Configures Flask for testing and returns a test client."""
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        # Reset the temporary inventory before each test to ensure isolation
        flask_app.temporary_inventory = [
            {"id": 1, "name": "Item A", "quantity": 100, "Barcode": "1234567890123", "Price": 9.99},
            {"id": 2, "name": "Item B", "quantity": 200, "Barcode": "1234567890124", "Price": 19.99}
        ]
        yield client


# PART 1: FLASK API ENDPOINT TESTS

def test_get_all_inventory(client):
    """Test GET /inventory retrieves all items."""
    response = client.get('/inventory')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert data[0]['name'] == "Item A"

def test_get_single_item(client):
    """Test GET /inventory/<id> for a valid and invalid ID."""
    # Valid ID
    response = client.get('/inventory/1')
    assert response.status_code == 200
    assert response.get_json()['name'] == "Item A"

    # Invalid ID
    response = client.get('/inventory/999')
    assert response.status_code == 404

def test_post_item_local(client):
    """Test POST /inventory creating an item without external lookup."""
    payload = {"name": "Item C", "quantity": 50, "Barcode": "11111", "Price": 5.00}
    response = client.post('/inventory', json=payload)
    assert response.status_code == 201
    
    data = response.get_json()
    assert data['item']['id'] == 3
    assert data['item']['name'] == "Item C"

def test_patch_item(client):
    """Test PATCH /inventory/<id> updates specific fields."""
    payload = {"quantity": 150, "Price": 12.99}
    response = client.patch('/inventory/1', json=payload)
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['updated_data']['quantity'] == 150
    assert data['updated_data']['Price'] == 12.99
    # Ensure ID hasn't changed
    assert data['updated_data']['id'] == 1

def test_delete_item(client):
    """Test DELETE /inventory/<id> removes item from list."""
    response = client.delete('/inventory/1')
    assert response.status_code == 200
    
    # Confirm it's gone
    get_response = client.get('/inventory/1')
    assert get_response.status_code == 404


# PART 2: EXTERNAL API INTERACTION TESTS

@patch('App.main.requests.get')
def test_external_api_success(mock_get, client):
    """Test Open Food Facts lookup successfully returns data on POST."""
    # Mocking successful API response payload structural match from Open Food Facts
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": 1,
        "product": {"product_name": "Mocked External Nutella"}
    }
    mock_get.return_value = mock_response

    # Send a request with ONLY a barcode, triggering external fetch logic
    payload = {"Barcode": "3017620422003", "quantity": 5}
    response = client.post('/inventory', json=payload)
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['item']['name'] == "Mocked External Nutella"
    assert data['item']['Price'] == 5.00  # Our hardcoded fallback default price

@patch('App.main.requests.get')
def test_external_api_failure(mock_get, client):
    """Test that app gracefully handles external API downtime/failures."""
    # Simulate a network connection drop/timeout error
    mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

    payload = {"Barcode": "3017620422003", "quantity": 5}
    response = client.post('/inventory', json=payload)
    
    # Server should not crash, it should fallback to "Unknown Product"
    assert response.status_code == 201
    data = response.get_json()
    assert data['item']['name'] == "Unknown Product"


# PART 3: CLI COMMANDS TESTS (MOCKED INPUTS)

@patch('cli_tool.requests.get')
def test_cli_get_all_items(mock_requests_get):
    """Test that CLI fetches and formats table data successfully."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"id": 1, "name": "Item A", "quantity": 100, "Barcode": "123", "Price": 9.99}
    ]
    mock_requests_get.return_value = mock_response

    cli_tool.get_all_items()
    mock_requests_get.assert_called_once_with("http://127.0.0.1:5000/inventory", timeout=5)

@patch('cli_tool.input')
@patch('cli_tool.requests.patch')
def test_cli_update_item_validation(mock_patch, mock_input):
    """Test CLI field updates and basic validation."""
    # Mock inputs simulating selecting item 1, leaving quantity blank, setting price to 15.50
    mock_input.side_effect = ["1", "", "15.50"]
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_patch.return_value = mock_response

    cli_tool.update_item()
    
    # Verify the payload built only includes fields that were given valid values
    mock_patch.assert_called_once_with(
        "http://127.0.0.1:5000/inventory/1", 
        json={"Price": 15.50}, 
        timeout=5
    )

