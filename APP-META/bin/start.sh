#!/bin/bash --login

echo "hello"

cd /home/admin/$APP_NAME/target/$APP_NAME/

main --create_tables
