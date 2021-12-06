batch_cmd += ' --account-name {acc_n} --account-key "{acc_k}" --account-endpoint {acc_u}'  
cdn 只 check 参数
C:\Code\azure-cli\src\azure-cli\azure\cli\command_modules\storage\tests\storage_test_util.py
C:\Code\azure-cli\src\azure-cli-testsdk\azure\cli\testsdk\base.py 

ENV_COMMAND_COVERAGE = 'AZURE_CLI_TEST_COMMAND_COVERAGE'
COVERAGE_FILE = 'az_command_coverage.txt'
if os.environ.get(ENV_COMMAND_COVERAGE, None):
	with open(COVERAGE_FILE, 'a') as coverage_file:
		if command.startswith('az '):
			command = command[3:]
		coverage_file.write(command + '\n')

C:\Code\az_command_coverage.txt
C:\Users\zelinwang\.azdev\tested_command.txt