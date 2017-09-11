from database import Storage

s = Storage()

print ('Enter api_id:')
api_id = input()
print ('Enter api_hash:')
api_hash = input()

s.register_api(api_id, api_hash)
