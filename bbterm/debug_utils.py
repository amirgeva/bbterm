diagnostics=False

def diagnostic_dump(data):
	if diagnostics:
		if data is None:
			with open('dump.bin', 'wb') as f:
				pass  # Clear the dump file
		else:
			with open('dump.bin', 'ab') as f:
				f.write(data)

def diag(message):
	if diagnostics:
		print(message)

