# Real Estate Lambdas

---

This project scrapes various real estate websites, with one lambda for each website, to get listings based on provided filters.

These listings are stored in a Dynamodb table.

The `NotificationLambda` function queries the table for recently added listings, and publishes to an SNS Topic, which notifies subscribed users of these new listings through SMS and email.

These lambdas are orchrestated with Step Functions, with the web scraping lambdas running in parallel, and `NotificationLambda` running after.

An AWS EventBridge Rule is used to trigger the execute the step function every hour of every day from 8 AM to 10 PM CST.

**CloudFormation YAML Template is WIP**
