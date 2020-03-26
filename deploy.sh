echo -e "3\nIndigo\nY\n1\nn\nn" | eb init -i
eb create indigo-webserver
aws codepipeline create-pipeline --cli-input-json file://pipeline.json