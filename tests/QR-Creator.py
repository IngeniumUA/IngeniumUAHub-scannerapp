import qrcode


"""
Creates qr-code for an event with the to check event and credentials
If qr-code is scanned, a string will be returned with in the syntax '*event*, *mail*'
This string can be parsed with the database to get the validity of the item
Validity can be *Valid*, *Invalid*, *Used* and if the item does not exist *NotPaid*
"""
##############################
# created in ticket creation
##############################
uuid = '0a56c773-bb2b-499b-ade0-b4b7eeb24345'

##############################
# create qr-code
##############################
testqr = qrcode.make(uuid)
testqr.save(uuid+".png")
