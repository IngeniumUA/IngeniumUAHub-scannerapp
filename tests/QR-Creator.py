import qrcode
import io
import PIL.Image as Image
import base64


"""
Creates qr-code for an event with the to check event and credentials
If qr-code is scanned, a string will be returned with in the syntax '*event*, *mail*'
This string can be parsed with the database to get the validity of the item
Validity can be *Valid*, *Invalid*, *Used* and if the item does not exist *NotPaid*
"""
##############################
# created in ticket creation
##############################
uuid = 'c663cdfb-4987-4acf-960e-88a5de7adc75'

##############################
# create qr-code
##############################
testqr = qrcode.make(uuid)
testqr.save(uuid+".png")

# convert img to base64 string
buffered = io.BytesIO()
testqr.save(buffered, format="PNG")
testqr_base64 = base64.urlsafe_b64encode(buffered.getvalue())

# check that the bytearray worked by converting it back to an img
print(testqr_base64)
print(buffered.getvalue())
image = Image.open(io.BytesIO(buffered.getvalue()))
image.save("test.png", "PNG")
