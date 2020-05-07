find . -maxdepth 1 -type f -name "*.py" | while read line; do
    echo $line
    pycodestyle $line
done
