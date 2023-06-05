[[ -e CLI ]] && rm -rf CLI
azdev command-change meta-export CLI --meta-output-path ./CLI
if [ $? -ne 0 ]; then
		echo "test cli meta generation failed, pass"
else
		echo "test cli meta generation succeed"
fi