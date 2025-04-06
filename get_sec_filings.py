from sec_api import QueryApi

# Set your SEC API key (You can get it after registering on sec-api.com)
api_key = "your_sec_api_key"

# Initialize the Query API client with your API key
query_api = QueryApi(api_key)

# Example: Create a query to fetch 10-K filings for a specific company (e.g., Apple Inc)
query = {
    "query": {
        "query_string": "10-K AND companyName:\"Apple Inc.\""
    },
    "from": 0,
    "size": 5
}

# Perform the query and get the results
result = query_api.get_filings(query)

# Print the result
print(result)
