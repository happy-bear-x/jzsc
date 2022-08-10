import base64
from Crypto.Cipher import AES


class AESDecrypt:
    iv = '0123456789ABCDEF'
    key = 'jo8j9wGw%6HbxfFn'

    @classmethod
    def _pkcs7unpadding(cls, text):
        """
        处理使用PKCS7填充过的数据
        :param text: 解密后的字符串
        :return:
        """
        length = len(text)
        unpadding = ord(text[length - 1])
        return text[0:length - unpadding]

    @classmethod
    def decrypt(cls, content):
        """
        AES解密，模式cbc，去填充pkcs7
        :param content: 16进制编码的加密字符串
        :return: 返回解密后的字符串
        """
        key = bytes(cls.key, encoding='utf-8')
        iv = bytes(cls.iv, encoding='utf-8')
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypt_bytes = cipher.decrypt(bytes.fromhex(content))
        result = str(decrypt_bytes, encoding='utf-8')
        result = cls._pkcs7unpadding(result)
        return result


if __name__ == '__main__':
    en_str = '95780ba0943730051dccb5fe3918f9fe71259a58aaeb83a18709429b26fca283a56bfdae74d48de952e0b4a1bbbf6d063273905d5346048f12a2555671f3245203b7cc4b59bf9dd69d317755f3e01d3541710af45a9cb1ec72131c0fe756fca5'
    de = AESDecrypt.decrypt(en_str)
    print(de)
