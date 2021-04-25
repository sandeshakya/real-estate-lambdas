from aws_cdk import (
    core as cdk,
    aws_lambda,
    aws_dynamodb,
    aws_stepfunctions,
    aws_stepfunctions_tasks,
    aws_sns,
    aws_sns_subscriptions,
)

HOME_SEARCH_TABLE = "dev-home_search_table"
POINT2HOMES_WEBSCRAPER = "dev-point2homes-webscraper"
REMAX_WEBSCRAPER = "dev-remax-webscraper"
SASKHOUSES_WBSCRAPER = "dev-saskhouses-webscraper"
NOTIFICATION_LAMBDA = "dev-NotificationsLambda"


class CdkStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        # create table
        home_search_table = aws_dynamodb.Table(
            self,
            HOME_SEARCH_TABLE,
            table_name=HOME_SEARCH_TABLE,
            partition_key=aws_dynamodb.Attribute(
                name="id", type=aws_dynamodb.AttributeType.STRING
            ),
        )
        home_search_table.add_global_secondary_index(
            index_name="type-createdat-index",
            partition_key=aws_dynamodb.Attribute(
                name="type", type=aws_dynamodb.AttributeType.STRING
            ),
            sort_key=aws_dynamodb.Attribute(
                name="createdat", type=aws_dynamodb.AttributeType.NUMBER
            ),
        )

        # sns topic
        notification_topic = aws_sns.Topic(
            self,
            "notificationTopic",
        )

        notification_topic.add_subscription(
            subscription=aws_sns_subscriptions.EmailSubscription(
                "sandeshakya94@gmail.com"
            )
        )

        point2homes = aws_lambda.Function(
            self,
            POINT2HOMES_WEBSCRAPER,
            function_name=POINT2HOMES_WEBSCRAPER,
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            handler="index.handler",
            code=aws_lambda.Code.asset("../point2homes-webscraper/src"),
        )
        point2homes.add_environment(
            key="TABLE_NAME", value=home_search_table.table_name
        )

        remax = aws_lambda.Function(
            self,
            REMAX_WEBSCRAPER,
            function_name=REMAX_WEBSCRAPER,
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            handler="index.handler",
            code=aws_lambda.Code.asset("../remax-webscraper/src"),
        )
        remax.add_environment(key="TABLE_NAME", value=home_search_table.table_name)

        saskhouses = aws_lambda.Function(
            self,
            SASKHOUSES_WBSCRAPER,
            function_name=SASKHOUSES_WBSCRAPER,
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            handler="index.handler",
            code=aws_lambda.Code.asset("../remax-webscraper/src"),
        )
        saskhouses.add_environment(key="TABLE_NAME", value=home_search_table.table_name)
        notificationlambda = aws_lambda.Function(
            self,
            NOTIFICATION_LAMBDA,
            function_name=NOTIFICATION_LAMBDA,
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            handler="index.handler",
            code=aws_lambda.Code.asset("../NotificationsLambda/src"),
        )
        notificationlambda.add_environment(
            key="TABLE_NAME", value=home_search_table.table_name
        )

        home_search_table.grant_write_data(point2homes)
        home_search_table.grant_write_data(remax)
        home_search_table.grant_write_data(saskhouses)
        home_search_table.grant_read_data(notificationlambda)
        notification_topic.grant_publish(notificationlambda)

        # step function
        # tasks
        saskhousesTask = aws_stepfunctions_tasks.LambdaInvoke(
            self,
            "saskhousesTask",
            lambda_function=saskhouses,
            payload=aws_stepfunctions.TaskInput.from_object(
                {"minPrice": 350000, "maxPrice": 480000, "bedsMin": 3, "bedsMax": 5}
            ),
        )
        remaxTask = aws_stepfunctions_tasks.LambdaInvoke(
            self,
            "remaxTask",
            lambda_function=remax,
            payload=aws_stepfunctions.TaskInput.from_object(
                {"minPrice": 350000, "maxPrice": 480000, "minBeds": 3, "minBaths": 3}
            ),
        )
        point2homesTask = aws_stepfunctions_tasks.LambdaInvoke(
            self,
            "point2homesTask",
            lambda_function=point2homes,
            payload=aws_stepfunctions.TaskInput.from_object(
                {
                    "location": "Saskatoon",
                    "PriceMin": "350000",
                    "PriceMax": "480000",
                    "Bedrooms": "3plus",
                    "PropertyType": "House",
                    "Bathrooms": "3-4",
                    "YearBuiltMin": "2000",
                }
            ),
        )
        notificationTask = aws_stepfunctions_tasks.LambdaInvoke(
            self,
            "notificationTask",
            lambda_function=notificationlambda,
        )

        parallelTasks = aws_stepfunctions.Parallel(self, "parallelTasks")
        parallelTasks.branch(remaxTask)
        parallelTasks.branch(saskhousesTask)
        parallelTasks.branch(point2homesTask)
        parallelTasks.next(notificationTask)

        aws_stepfunctions.StateMachine(self, "StateMachine", definition=parallelTasks)
