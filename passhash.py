from passlib.hash import sha512_crypt

password = "admin123!!!"
hashed_password = sha512_crypt.hash(password)

print(hashed_password)
