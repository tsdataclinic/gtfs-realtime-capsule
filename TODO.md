# TODO

- create Lake
    - crawler
    -   work off new scraped data for now
- migrate Grabber
    - rewrite for UTC time
- migrate API
    - localize timestamps on return




requirements for new stack
- creates and configures Event Rules for each feed
- creates a governed db lakeformation
- create a governed table and crawls for each feed only if table doesn’t exist (eg check if table exists)
- deploys the grabber lambda
- deploys the API lambda
- creates a gateway
- maps custom domain to the gateway


https://marcqualie.com/2017/05/write-only-s3-permissions
https://www.dionysopoulos.me/safer-backups-with-write-only-amazon-s3-credentials.html

