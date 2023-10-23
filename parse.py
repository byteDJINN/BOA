from struct import unpack
from io import BytesIO
import math
import binascii
from schema import PidTagSchema
import json
import re 
# this is the table of tags and codes

def hexify(PropID):
  return "{0:#0{1}x}".format(PropID, 10).upper()[2:]

def lookup(ulPropID):
  if hexify(ulPropID) in PidTagSchema:
    (PropertyName, PropertyType) = PidTagSchema[hexify(ulPropID)]
    return PropertyName
  else:
    return hex(ulPropID)

d = {}

# When reading a binary file, always add a 'b' to the file open mode
with open('udetails.oab', 'rb') as f:
  (ulVersion, ulSerial, ulTotRecs) = unpack('<III', f.read(4 * 3))
  assert ulVersion == 32, 'This only supports OAB Version 4 Details File'
  print("Total Record Count: ", ulTotRecs)
  # OAB_META_DATA
  cbSize = unpack('<I', f.read(4))[0]
  # print "OAB_META_DATA",
  meta = BytesIO(f.read(cbSize - 4))
  # the length of the header attributes
  # we don't know and don't really need to know how to parse these
  HDR_cAtts = unpack('<I', meta.read(4))[0]
  print("rgHdrAtt HDR_cAtts",HDR_cAtts)
  for rgProp in range(HDR_cAtts):
    ulPropID = unpack('<I', meta.read(4))[0]
    ulFlags  = unpack('<I', meta.read(4))[0]
    # print rgProp, lookup(ulPropID), ulFlags
  # these are the attributes that we actually care about
  OAB_cAtts = unpack('<I', meta.read(4))[0]
  OAB_Atts = []
  print("rgOabAtts OAB_cAtts", OAB_cAtts)
  for rgProp in range(OAB_cAtts):
    ulPropID = unpack('<I', meta.read(4))[0]
    ulFlags  = unpack('<I', meta.read(4))[0]
    # print rgProp, lookup(ulPropID), ulFlags
    OAB_Atts.append(ulPropID)
  print("Actual Count", len(OAB_Atts))
  # OAB_V4_REC (Header Properties)
  cbSize = unpack('<I', f.read(4))[0]
  f.read(cbSize - 4)

  # now for the actual stuff
  counter = 0
  percent = 0
  prev_percent = 0
  while counter < 200000:
    counter += 1
    percent = int((counter / 200000) * 100)
    if percent != prev_percent:
      prev_percent = percent
      print(percent, "%")
    try:
      read = f.read(4)
      if read == '':
        break
      # this is the size of the chunk, incidentally its inclusive
      cbSize = unpack('<I', read)[0]
      # so to read the rest, we subtract four
      chunk = BytesIO(f.read(cbSize - 4))
      # wow such bit op
      presenceBitArray = bytearray(chunk.read(int(math.ceil(OAB_cAtts / 8.0))))
      indices = [i for i in range(OAB_cAtts) if (presenceBitArray[i // 8] >> (7 - (i % 8))) & 1 == 1]
      #print("\n----------------------------------------")
      # print "Chunk Size: ", cbSize

      def read_str():
        # strings in the OAB format are null-terminated
        buf = b""
        while True:
          n = chunk.read(1)
          if n == b"\0" or n == b"":
            break
          buf += n
        return buf.decode('utf-8') # problem here
        # return unicode(buf, errors="ignore")

      def read_int():
        # integers are cool aren't they
        byte_count = unpack('<B', chunk.read(1))[0]
        if 0x81 <= byte_count <= 0x84:
          byte_count = unpack('<I', (chunk.read(byte_count - 0x80) + b"\0\0\0")[0:4])[0]
        else:
          if byte_count > 127:
            return -1
        return byte_count

      rec = {}

      for i in indices:
        PropID = hexify(OAB_Atts[i])
        if PropID not in PidTagSchema:
          continue
          raise ValueError("This property id (" + PropID + ") does not exist in the schema")

        (Name, Type) = PidTagSchema[PropID]

        if Type == "PtypString8" or Type == "PtypString":
          val = read_str()
          rec[Name] = val
          #print(Name, val)
        elif Type == "PtypBoolean":
          val = unpack('<?', chunk.read(1))[0]
          rec[Name] = val
          #print (Name, val)
        elif Type == "PtypInteger32":
          val = read_int()
          rec[Name] = val
          #print(Name, val)
        elif Type == "PtypBinary":
          bin = chunk.read(read_int())
          rec[Name] = binascii.b2a_hex(bin)
          #print(Name, len(bin), binascii.b2a_hex(bin))
        elif Type == "PtypMultipleString" or Type == "PtypMultipleString8":
          byte_count = read_int()
          #print (Name, byte_count)
          arr = []
          for i in range(byte_count):
            val = read_str()
            arr.append(val)
            #print(i, "\t", val)
          rec[Name] = arr
    
        elif Type == "PtypMultipleInteger32":
          byte_count = read_int()
          #print(Name, byte_count)
          arr = []
          for i in range(byte_count):
            val = read_int()
            if Name == "OfflineAddressBookTruncatedProperties":
              val = hexify(val)
              if val in PidTagSchema:
                val = PidTagSchema[val][0]
            arr.append(val)
            #print(i, "\t", val)

          rec[Name] = arr

        elif Type == "PtypMultipleBinary":
          byte_count = read_int()
          #print(Name, byte_count)
          arr = []
          for i in range(byte_count):
            bin_len = read_int()
            bin = chunk.read(bin_len)
            arr.append(binascii.b2a_hex(bin))
            #print(i, "\t", bin_len, binascii.b2a_hex(bin))
          rec[Name] = arr
        else:
          raise "Unknown property type (" + Type + ")"
        
        if Name == "DisplayName":
          # check if name matches regex [A-Za-z with space] ([0-9]) get match of the first and second part assign to varibles
          a = re.match(r"^([A-Za-z ]+) (\([0-9]+\))$", val)
          if a:
            d[a.group(1)] = a.group(2)[1:-1]
          
        
      remains = chunk.read()
    except:
      pass
json_out = open('test.json', 'w')
json_out.write(json.dumps(d, indent=4))
json_out.close()
    
