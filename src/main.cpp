// This example code is in the Public Domain (or CC0 licensed, at your option.)
// By Evandro Copercini - 2018
//
// This example creates a bridge between Serial and Classical Bluetooth (SPP)
// and also demonstrate that SerialBT have the same functionalities of a normal Serial

#include "BluetoothSerial.h"
#include <mbedtls/pk.h>
#include <mbedtls/ctr_drbg.h>
#include <mbedtls/entropy.h>
#include <mbedtls/base64.h>

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled! Please run `make menuconfig` to and enable it
#endif
// ------------------------------------------------------------------
const String SEPERATOR = "\n";

const char *private_key_pem = R"(
-----BEGIN RSA PRIVATE KEY-----
MIICWgIBAAKBgFs44W15Opn0ruNjtl8fY6eNmQir3AsKqj2UmZ7ShLegwob3oN1l
sn0keL401eOzjv2t7ObD/stszZao4Ugmccb83ITjEmfvHgH5rixn4+WT8sa3KW26
5IrnlfHjVRpGxRqGISf9ClyiK01acc+2EbUHqXyP+JYQwWf4+ooCYDgFAgMBAAEC
gYAiQxfwTTMkdhFl2KK70YdVfEp5RktsXkIYxQJ586njal8F4GYsIbFLbXJoRmH7
lwpi33t2JTFC6IfDSYTr23yqBJ/6DKiCa4ZsSQPd06iqz2aDHc4Bq7D2ZQMdkOMK
vpCHpTUgKW1sHYLzqzGMURMHkqBvGA39qZ3TbdBZmZuk9QJBAJ2WoSiis3FA8YUm
digwYxNepdyxXQu5f6DQm9HItMKK/BqmnL8x46nJbVZGednxN02mlzyDjG7lipUv
4LfQoHMCQQCUMGf9rZB8ZhP3RNx+wz2HFfVl8b38PLaJQ6E4WFj6Xrmnx/11+B1V
yRWbWAJZueBa3DMf4cOMtdIOsH18d/+nAkBDEhoTRnQjDqX8qqr9XeK9GrpzHJXi
aJf2ZPL8rXSpnCfCXAk4os4ntFAxuRshdDW6ed3CZqa9iDqcVl1JPqUbAkAkyfen
JMWv/G+MfY338mR9+teXXXJ7Al+WqDGIGXbNgWK54o5sERLHT0qL7Ed5Gwo1xGD0
00mGz0S83NfqZKgVAkA1FRhnKSKeTIApLSF0czX+CkO5b94wvB+UEj0BBLgCZOjr
FtM5YV3W2Q/dvCxcRie65sHIil4B7E4D7pzKf1aK
-----END RSA PRIVATE KEY-----
)";

const char *public_key_pem = R"(
-----BEGIN PUBLIC KEY-----
MIGeMA0GCSqGSIb3DQEBAQUAA4GMADCBiAKBgFs44W15Opn0ruNjtl8fY6eNmQir
3AsKqj2UmZ7ShLegwob3oN1lsn0keL401eOzjv2t7ObD/stszZao4Ugmccb83ITj
EmfvHgH5rixn4+WT8sa3KW265IrnlfHjVRpGxRqGISf9ClyiK01acc+2EbUHqXyP
+JYQwWf4+ooCYDgFAgMBAAE=
-----END PUBLIC KEY-----
)";

String encrypt_message(const String &message, const char *public_key_pem);
String decrypt_message(const String &encrypted_message, const char *private_key_pem);
void send_message(const String &msg_to_send);
void on_receive_message(const String &msg_received);
bool endsWith(const std::string &str, const std::string &suffix);
std::string remove_last_n_chars(const std::string &str, int n);
bool is_base64(const String &str);
bool is_base64(const unsigned char *str, size_t length);
String base64_encode(const unsigned char *data, size_t length);
String base64_decode(const String &encoded_string);
// ------------------------------------------------------------------
BluetoothSerial SerialBT;

void setup()
{
  Serial.begin(9600);
  SerialBT.begin("ESP32"); // Bluetooth device name
  Serial.println("The device started, now you can pair it with bluetooth!");
}

std::string msgToSendBuffer = "";
std::string msgReceivedBuffer = "";

void loop()
{
  while (Serial.available())
  {
    char c = Serial.read();
    msgToSendBuffer += c;
    if (endsWith(msgToSendBuffer, SEPERATOR.c_str()))
    {
      String msg = String(remove_last_n_chars(msgToSendBuffer, SEPERATOR.length()).c_str());
      send_message(msg);
      msgToSendBuffer = "";
    }
  }
  while (SerialBT.available())
  {
    char c = SerialBT.read();
    msgReceivedBuffer += c;
    if (endsWith(msgReceivedBuffer, SEPERATOR.c_str()))
    {
      String received_msg = String(remove_last_n_chars(msgReceivedBuffer, SEPERATOR.length()).c_str());
      on_receive_message(received_msg);
      msgReceivedBuffer = "";
    }
  }
}

// ------------------------------------------------------------------
void send_message(const String &msg_to_send)
{
  Serial.print(">>> Sending Encrypted Message:\n--------------{ Clear Message }\n"+msg_to_send);
  String encrypted_message = encrypt_message(msg_to_send, public_key_pem);
  if (!encrypted_message.isEmpty())
  {
    // Send `encrypted_message` through your communication channel
    Serial.print("\n--------------{ Encrypted Base64 Message }\n" + encrypted_message + "\n--------------|END|\n\n");
    SerialBT.print(encrypted_message + SEPERATOR);

  }
  else
  {
    Serial.println("Failed to encrypt message.");
  }
}
void on_receive_message(const String &msg_received)
{
  Serial.print("<<< Receiving Encrypted Message:\n--------------{ Encrypted Base64 Message }\n"+msg_received);
  String decrypted_message = decrypt_message(msg_received, private_key_pem);
  if (!decrypted_message.isEmpty())
  {
    Serial.println("\n--------------{ Clear Message }\n" + decrypted_message + "\n--------------|END|\n\n");
  }
  else
  {
    Serial.println("Failed to decrypt message.");
  }
}

String encrypt_message(const String &message, const char *public_key_pem)
{
  mbedtls_pk_context pk;
  mbedtls_pk_init(&pk);
  mbedtls_ctr_drbg_context ctr_drbg;
  mbedtls_ctr_drbg_init(&ctr_drbg);
  mbedtls_entropy_context entropy;
  mbedtls_entropy_init(&entropy);

  const char *pers = "rsa_encrypt";
  mbedtls_ctr_drbg_seed(&ctr_drbg, mbedtls_entropy_func, &entropy,
                        reinterpret_cast<const unsigned char *>(pers), strlen(pers));

  if (mbedtls_pk_parse_public_key(&pk, (const unsigned char *)public_key_pem, strlen(public_key_pem) + 1) != 0)
  {
    Serial.println("Failed to parse public key.");
    return "";
  }

  size_t encrypted_size = mbedtls_pk_get_len(&pk);
  unsigned char encrypted[encrypted_size];
  size_t olen = 0;

  if (mbedtls_pk_encrypt(&pk, (const unsigned char *)message.c_str(), message.length(),
                         encrypted, &olen, sizeof(encrypted),
                         mbedtls_ctr_drbg_random, &ctr_drbg) != 0)
  {
    Serial.println("Encryption failed.");
    return "";
  }

  mbedtls_pk_free(&pk);
  mbedtls_ctr_drbg_free(&ctr_drbg);
  mbedtls_entropy_free(&entropy);

  return base64_encode(encrypted, olen);
}

String decrypt_message(const String &encrypted_base64_message, const char *private_key_pem)
{
  String encrypted_message = base64_decode(encrypted_base64_message);
  mbedtls_pk_context pk;
  mbedtls_pk_init(&pk);

  if (mbedtls_pk_parse_key(&pk, (const unsigned char *)private_key_pem, strlen(private_key_pem) + 1, nullptr, 0) != 0)
  {
    Serial.println("Failed to parse private key.");
    return "";
  }

  size_t encrypted_size = encrypted_message.length();
  unsigned char decrypted[encrypted_size];
  size_t olen = 0;

  if (mbedtls_pk_decrypt(&pk, (const unsigned char *)encrypted_message.c_str(), encrypted_size,
                         decrypted, &olen, sizeof(decrypted),
                         nullptr, nullptr) != 0)
  {
    Serial.println("Decryption failed.");
    return "";
  }

  mbedtls_pk_free(&pk);

  return String((char *)decrypted, olen);
}

bool endsWith(const std::string &str, const std::string &suffix)
{
  if (str.length() < suffix.length())
  {
    return false;
  }
  return str.compare(str.length() - suffix.length(), suffix.length(), suffix) == 0;
}
std::string remove_last_n_chars(const std::string &str, int n)
{
  if (n <= 0)
  {
    return str; // If n is zero or negative, return the original string
  }
  if (n >= str.length())
  {
    return ""; // If n is greater than or equal to the string length, return an empty string
  }
  return str.substr(0, str.length() - n); // Return the string without the last n characters
}

bool is_base64(const String &str)
{
  // Check if the string length is a multiple of 4
  if (str.length() % 4 != 0)
  {
    Serial.println("String length is not a multiple of 4.");
    return false;
  }

  // Check if the string contains only valid base64 characters
  for (size_t i = 0; i < str.length(); ++i)
  {
    char c = str.charAt(i);
    if (!((c >= 'A' && c <= 'Z') ||
          (c >= 'a' && c <= 'z') ||
          (c >= '0' && c <= '9') ||
          (c == '+') ||
          (c == '/') ||
          (c == '=')))
    {
      Serial.print("Invalid base64 character found: ");
      Serial.println("found:<"+String(c)+"> at index: <"+String(i)+">");
      return false;
    }
  }

  return true;
}
bool is_base64(const unsigned char *str, size_t length)
{
  if (length % 4 != 0)
  {
    Serial.println("String length is not a multiple of 4.");
    return false;
  }

  for (size_t i = 0; i < length; ++i)
  {
    unsigned char c = str[i];
    if (!((c >= 'A' && c <= 'Z') ||
          (c >= 'a' && c <= 'z') ||
          (c >= '0' && c <= '9') ||
          (c == '+') ||
          (c == '/') ||
          (c == '=')))
    {
      Serial.print("Invalid base64 character found: ");
      Serial.println("found:<"+String(c)+"> at index: <"+String(i)+">");

      return false;
    }
  }

  return true;
}

String base64_encode(const unsigned char *data, size_t length)
{
  // Calculate the length of the encoded string
  size_t encoded_length = 4 * ((length + 2) / 3);
  char *encoded_data = new char[encoded_length + 1]; // +1 for null terminator

  // Encode the data
  size_t output_length = 0;
  if (mbedtls_base64_encode(reinterpret_cast<unsigned char *>(encoded_data), encoded_length + 1, &output_length, data, length) != 0)
  {
    Serial.println("Base64 encoding failed.");
    delete[] encoded_data;
    return "";
  }

  String encoded_string = String(encoded_data);
  delete[] encoded_data;
  return encoded_string;
}
String base64_decode(const String &encoded_string)
{
  size_t encoded_length = encoded_string.length();
  size_t decoded_length = (encoded_length / 4) * 3;
  unsigned char *decoded_data = new unsigned char[decoded_length];

  size_t output_length = 0;
  if (mbedtls_base64_decode(decoded_data, decoded_length, &output_length,
                            reinterpret_cast<const unsigned char *>(encoded_string.c_str()), encoded_length) != 0)
  {
    Serial.println("Base64 decoding failed.");
    is_base64(encoded_string);
    delete[] decoded_data;
    return "";
  }

  String decoded_string = String(reinterpret_cast<char *>(decoded_data), output_length);
  delete[] decoded_data;
  return decoded_string;
}
// ------------------------------------------------------------------