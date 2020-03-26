echo -e "3\nIndigo\nY\n1\nn\nn" | eb init -i --profile pa_iam
eb create indigo-webserver
aws codepipeline create-pipeline --cli-input-json file://pipeline.json --profile pa_iam