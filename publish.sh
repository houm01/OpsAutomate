#/usr/bin/bash

VERSION=$1

# sed -i 's/replace_this/$VERSION/g' setup.py

git add .
git commit -m "Released v$VERSION"

git tag -a v$VERSION -m v$VERSION

git push --tag
git push
