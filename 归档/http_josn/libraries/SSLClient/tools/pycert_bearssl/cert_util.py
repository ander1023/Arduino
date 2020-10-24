# Utility functions for a Python SSL certificate conversion tool.
# These functions are in this file so the can also be used in
# A web API implementing this tool.
# Author: Tony DiCola, Modified by Noah Koontz
# 
# Dependencies:
#   click - Install with 'sudo pip install click' (omit sudo on windows)
#   PyOpenSSL - See homepage: https://pyopenssl.readthedocs.org/en/latest/
#               Should just be a 'sudo pip install pyopenssl' command, HOWEVER
#               on Windows you probably need a precompiled binary version.  Try
#               installing with pip and if you see errors when running that
#               OpenSSL can't be found then try installing egenix's prebuilt
#               PyOpenSSL library and OpenSSL lib:
#                 http://www.egenix.com/products/python/pyOpenSSL/
#   certifi - Install with 'sudo pip install certifi' (omit sudo on windows)

import re
from OpenSSL import SSL, crypto
import socket
import textwrap
import math
import os

CERT_PATTERN = re.compile("^\-\-\-\-\-BEGIN CERTIFICATE\-\-\-\-\-[a-z,A-Z,0-9,\n,\/,+]+={0,2}\n\-\-\-\-\-END CERTIFICATE-\-\-\-\-", re.MULTILINE)

# Default name prefixes for varibles used in the hearder autogeneration
# Autogenerator will follow these names with a number
# e.g. "TA_DN0"
# Distinguished name array prefix
DN_PRE = "TA_DN"
# RSA public key number prefix
RSA_N_PRE = "TA_RSA_N"
# RSA public key exponent prefix
RSA_E_PRE = "TA_RSA_E"


# Template that defines the C header output format.
# This takes in a few named parameters:
#  - guard_name: Unique name to apply to the #ifndef header guard.
#  - cert_length_var: Variable/define name for the length of the certificate.
#  - cert_length: Length of the certificate (in bytes).
#  - cert_var: Variable name for the certificate data.
#  - cert_data: Certificate data, formatted as a bearssl trust anchor array
#  - cert_description: Any descriptive info about the certs to put in comments.
# NOTE: If you're changing the template make sure to escape all curly braces
# with a double brace (like {{ or }}) or else Python will try to interpret as a
# string format variable.
CFILE_TEMPLATE = """\
#ifndef _{guard_name}_H_
#define _{guard_name}_H_

#ifdef __cplusplus
extern "C"
{{
#endif

/* This file is auto-generated by the pycert_bearssl tool.  Do not change it manually.
 * Certificates are BearSSL br_x509_trust_anchor format.  Included certs:
 *
{cert_description}
 */

#define {cert_length_var} {cert_length}

{cert_data}

#ifdef __cplusplus
}} /* extern "C" */
#endif

#endif /* ifndef _{guard_name}_H_ */
"""

# Template that defines a static array of bytes
# This takes in a few named parameters:
#  - ray_type: The type (int, unsigned char) to use for the static array
#  - ray_name: The varible name of the static array
#  - ray_data: The comma seperated data of the array (ex. "0x12, 0x34, ...")
CRAY_TEMPLATE = """\
static const {ray_type} {ray_name}[] = {{
{ray_data}
}};"""

# Template that defines a single root certificate entry in the BearSSL trust
# anchor list
# This takes in a few named parameters:
#  - ta_dn_name: The name of the static byte array containing the distunguished
#    name of the certificate.
#  - rsa_number_name: Varible name of the static array containing the RSA number
#  - rsa_exp_name: Varible name of the static array containing the RSA exponent
CROOTCA_TEMPLATE = """\
    {{
        {{ (unsigned char *){ta_dn_name}, sizeof {ta_dn_name} }},
        BR_X509_TA_CA,
        {{
            BR_KEYTYPE_RSA,
            {{ .rsa = {{
                (unsigned char *){rsa_number_name}, sizeof {rsa_number_name},
                (unsigned char *){rsa_exp_name}, sizeof {rsa_exp_name},
            }} }}
        }}
    }},"""

# Template that defines a description of the certificate, so that the header
# file can be slightly more human readable
# This takes in a few named parameters:
#  - cert_num: The index used to represent the certificate to the computer
#  - cert_label: The certificate's name field (Usually CN, in the subject)
#  - cert_issue: The certificate's issuer string
#  - cert_subject: The certificate's subject string
#  - cert_domain: The domains polled by this tool that returned this certificate
CCERT_DESC_TEMPLATE = """\
 * Index:    {cert_num}
 * Label:    {cert_label}
 * Subject:  {cert_subject}"""

def PEM_split(cert_pem):
    """Split a certificate / certificate chain in PEM format into multiple
    PEM certificates.  This is useful for extracting the last / root PEM cert
    in a chain for example.  Will return a list of strings with each string
    being an individual PEM certificate (including its '-----BEGIN CERTIFICATE...'
    delineaters).
    """
    # Split cert based on begin certificate sections, then reconstruct as an
    # array of individual cert strings.
    return re.findall(CERT_PATTERN, cert_pem)

def parse_root_certificate_store(store):
    """Parses a list of trusted root certificates, which we
    can match to the respective certificates sent from the websites. The where
    parameter takes a loaded certificate file (certifi.where()),
    and the function returns a list of crypto.x509 objects.
    """
    # perform file operations
    certStore = PEM_split(store.read())
    # convert the raw PEM files into x509 object
    return [crypto.load_certificate(crypto.FILETYPE_PEM, pem) for pem in certStore]

def get_server_root_cert(address, port, certDict):
    """Attempt to retrieve the the root certificate in the full SSL cert chain 
    from the provided server address & port. The certDict parameter should
    contain a dictionary of { certificate.get_subject().hash() md5 hash : certificate }, 
    which this function will use to match the certificate chain to a stored root 
    certificate. This function will return a single certificate as a PyOpenSSL X509 
    object, or None if the chain couldn't be retrieved for some reason, or the 
    certDict did not contain a matching certificate.
    """
    # Use PyOpenSSL to initiate an SSL connection and get the full cert chain.
    # Sadly Python's built in SSL library can't do this so we must use this
    # OpenSSL-based library.
    cert = None
    ctx = SSL.Context(SSL.TLSv1_2_METHOD)
    # do the connection, and fetch the cert chain
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ssl_soc = SSL.Connection(ctx, soc)
    ssl_soc.connect((address, port))
    ssl_soc.set_tlsext_host_name(bytes(address, "utf8"))
    try:
        ssl_soc.do_handshake()
        cert = ssl_soc.get_peer_cert_chain()[-1]
    finally:
        ssl_soc.shutdown()
        soc.close()
    # match the certificate in the chain to the respective root certificate using the common name
    if cert == None:
        print("Failed to fetch certificate on domain: " + address)
        return None
    cn_hash = cert.get_issuer().hash()
    # if there is a respective certificate, return it
    # else print an error and return None
    if cn_hash not in certDict:
        print("Could not find matching root certificate for domain: " + address)
        return None
    return certDict[cn_hash]

def bytes_to_c_data(mah_bytes, length=None):
    """Converts a byte array to a CSV C array data format, with endlines!
        e.g: 0x12, 0xA4, etc.
        mah_bytes is the bytearray, and length is the number of bytes to
        generate in the array, and indent is how much to indent the output
    """
    ret = []
    # create an array of byte strings, including an endline every 10 or so bytes
    for i, bytestr in enumerate(textwrap.wrap(mah_bytes.hex(), 2)):
        ret.append("0x" + bytestr + ", ")
    # pad with extra zeros
    while length != None and len(ret) < length:
        ret.append("0x00, ")
    # join, wrap, and return
    return textwrap.fill(''.join(ret), width=6*12 + 5, initial_indent='    ', subsequent_indent='    ', break_long_words=False)

def decribe_cert_object(cert, cert_num, domain=None):
    """
    Formats a string describing a certificate object, including the domain
    being used and the index in the trust anchor array. Cert should be a
    x509 object, domain should be a string name, and cert_num should be
    an integer.
    """
    # get the label from the subject feild on the certificate
    label = ""
    com = dict(cert.get_subject().get_components())
    if b'CN' in com:
        label = com[b'CN'].decode("utf-8")
    elif b'OU' in com:
        label = com[b'OU'].decode("utf-8")
    elif b'O' in com:
        label = com[b'O'].decode("utf-8")
    # return the formated string
    crypto = cert.to_cryptography()
    out_str = CCERT_DESC_TEMPLATE.format(
        cert_num=cert_num,
        cert_label=label,
        cert_subject=crypto.subject.rfc4514_string(),
    )
    # if domain, then add domain entry
    if domain is not None:
        out_str += "\n * Domain(s): " + domain
    return out_str

def x509_to_header(x509Certs, cert_var, cert_length_var, output_file, keep_dupes, domains=None):
    """Combine a collection of PEM format certificates into a single C header with the
    combined cert data in BearSSL format.  x509Certs should be a list of pyOpenSSL x590 objects,
    domains should be a list of respective domain strings (in same order as x509Certs),
    cert_var controls the name of the cert data variable in the output header, cert_length_var 
    controls the name of the cert data length variable/define, output is the output file 
    (which must be open for writing). Keep_dupes is a boolean to indicate if duplicate 
    certificates should be left intact (true) or removed (false).
    """
    cert_description = ''
    certs = x509Certs
    # Save cert data as a C style header.
    # start by building each component
    cert_data = ""
    # hold an array of static array strings (TA_RSA_N)
    static_arrays = list()
    # same with CA entries
    CAs = list()
    # descriptions
    cert_desc = list()
    # track the serial numbers so we can find duplicates
    cert_ser = list()
    for i, cert in enumerate(certs):
        # calculate the index shifted from duplicates (if any)
        cert_index = len(CAs)
        # deduplicate certificates
        if not keep_dupes and cert.get_serial_number() in cert_ser:
            # append the domain we used it for into the cert description
            if domains is not None:
                cert_desc[cert_ser.index(cert.get_serial_number())] += ", " + domains[i]
            # we don't need to generate stuff for this certificate
            continue
        # record the serial number for later
        cert_ser.append(cert.get_serial_number())
        # add a description of the certificate to the array
        if domains is None:
            cert_desc.append(decribe_cert_object(cert, cert_index))
        else:
            cert_desc.append(decribe_cert_object(cert, cert_index, domain=domains[i]))
        # build static arrays containing all the keys of the certificate
        # start with distinguished name
        # get the distinguished name in bytes
        dn_bytes_str = bytes_to_c_data(cert.get_subject().der())
        static_arrays.append(CRAY_TEMPLATE.format(
            ray_type="unsigned char", 
            ray_name=DN_PRE + str(cert_index), 
            ray_data=dn_bytes_str))
        # next, the RSA public numbers
        pubkey = cert.get_pubkey()
        numbers = pubkey.to_cryptography_key().public_numbers()
        # starting with the modulous
        n_bytes_str = bytes_to_c_data(numbers.n.to_bytes(pubkey.bits() // 8, byteorder="big"))
        static_arrays.append(CRAY_TEMPLATE.format(
            ray_type="unsigned char", 
            ray_name=RSA_N_PRE + str(cert_index), 
            ray_data=n_bytes_str))
        # and then the exponent
        e_bytes_str = bytes_to_c_data(numbers.e.to_bytes(math.ceil(numbers.e.bit_length() / 8), byteorder="big"))
        static_arrays.append(CRAY_TEMPLATE.format(
            ray_type="unsigned char", 
            ray_name=RSA_E_PRE + str(cert_index), 
            ray_data=e_bytes_str))
        # format the root certificate entry
        CAs.append(CROOTCA_TEMPLATE.format(
            ta_dn_name=DN_PRE + str(cert_index), 
            rsa_number_name=RSA_N_PRE + str(cert_index), 
            rsa_exp_name=RSA_E_PRE + str(cert_index)))
    # concatonate it all into the big header file template
    # cert descriptions
    cert_desc_out = '\n * \n'.join(cert_desc)
    # static arrays
    cert_data_out = '\n\n'.join(static_arrays)
    cert_data_out += '\n\n' + CRAY_TEMPLATE.format(
        ray_type="br_x509_trust_anchor", 
        ray_name=cert_var, 
        ray_data='\n'.join(CAs))
    # create final header file
    output_file.write(CFILE_TEMPLATE.format(
        guard_name=os.path.splitext(output_file.name)[0].upper(),
        cert_description=cert_desc_out, 
        cert_length_var=cert_length_var,
        cert_length=str(len(CAs)),
        cert_data=cert_data_out,
    ))