source ~/.venv/mahjong-account-app-backend/bin/activate
last_element=$(basename "$1")
grep "def test_${last_element}.*(.*" "./tests/unit/test_handler.py" | awk -F"(" '{print $1}' | sed 's/def //' | while read -r testfuncname; do
    echo
    echo $testfuncname
    pytest -s ./tests/unit/test_handler.py::${testfuncname}
    echo
done
