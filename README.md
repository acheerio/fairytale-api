# Introduction
The Fairytale API is a resource for creating, editing, viewing, and deleting your **unicorns**. The **user** who creates a unicorn is its “friend.” Each unicorn can belong to up to one **blessing**, which is a group of unicorns (similar to a “flock” of birds). The user who creates a blessing is its “founder.”

# Getting Started
Visit this link to register or login and view your JWT:

https://fairytale-api.appspot.com

The app will redirect a logged-in user (based on the session) to https://fairytale-api.appspot.com/profile. If you are redirected and do not want to be (for example, you need to log back in with different credentials) or are receiving a refresh error, go to https://fairytale-api.appspot.com/logout, which will remove the old/stale information from the session. It will redirect you back to the homepage where you can log back in.

# Detailed Documentation
[Fairytale API Documentation](https://docs.google.com/document/d/1MzdlSst8s7ivWjsGDqC9a11WcUkhlr97rzZNZe-5e48/)

# Tests
A comprehensive Postman test suite is available to build upon.

To run the tests as-is, create/register two valid users with JWTs. Place the first user’s JWT in the “token” environmental variable of the Postman test suite. This is the user whose credentials will be used for most of the test suite. Place the second user’s JWT in the “forbidden_jwt” environmental variable. This is a valid JWT/user whose credentials will be used to produce the 403 Forbidden status code when the user attempts to modify/delete entities created by the first user.