def create_headers_token(setup_user_token_admin):
    # 1. Correctly retrieve the token value and type from the fixture
    access_token = setup_user_token_admin['access_token']
    token_type = setup_user_token_admin['token_type']

    # 2. Construct the headers dictionary in the correct format
    headers = {"Authorization": f"{token_type.capitalize()} {access_token}"}
    return headers