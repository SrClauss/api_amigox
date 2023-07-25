# Application Configuration

This document describes the necessary configurations to run the AmigoX application in your local environment.

## Environment Variables

Make sure to set the following environment variables before running the application:

- `DB_USER`: The username for the MySQL database.
- `DB_PASSWORD`: The password for the MySQL database.
- `SECRET_KEY`: The secret key used by Flask to encrypt cookies.
- `API_KEY`: The API key used for authentication.
- `DB_HOST`: The host of the MySQL database (usually "localhost").
- `DB_NAME`: The name of the main MySQL database.
- `TEST_DB_NAME`: The name of the MySQL database for running tests.
- `DB_PORT`: The port of the MySQL database (usually "3306").
- `FLASK_ENV`: The Flask execution environment (set to "test" for running tests).

## Database Configuration

The application uses a MySQL database to store data. Make sure you have MySQL installed in your development environment.

## Running the Application

To run the application, follow these steps:

1. Clone the AmigoX repository from GitHub.
2. Set up the environment variables listed above.
3. Create a virtual environment for the project (`python -m venv myenv`).
4. Activate the virtual environment (`source myenv/bin/activate`).
5. Install the project dependencies (`pip install -r requirements.txt`).
6. Run the application (`python run.py`).

## Running Tests

To run the application tests, follow these steps:

1. Make sure you have correctly set up the environment variables for running tests.
2. Activate the virtual environment (`source myenv/bin/activate`).
3. Run all tests (`python -m unittest discover tests`).

That's it! Now you are ready to run and test the AmigoX application in your local environment.
