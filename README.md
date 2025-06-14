# Flight Dispatcher

This application helps you find flight routes based on your aircraft, desired flight length, and airline. It uses the FlightRadar24 API for route suggestions and the SimBrief API to generate a detailed flight plan.

## Setup

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **SimBrief API Key:**
    -   Request an API key from SimBrief as per their [API documentation](https://forum.navigraph.com/t/the-simbrief-api/5298).
    -   When you get your API access, you will also receive a `simbrief.apiv1.js` file.
    -   Place the `simbrief.apiv1.js` file in the `flight-dispatcher/static/` folder.
    -   The application will then use your SimBrief account to generate flight plans.

3.  **Run the application:**
    ```bash
    flask run
    ``` 