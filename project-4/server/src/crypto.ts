import crypto from "crypto";

// Diffie-Hellman parameters
const DH_P = 104729;
const DH_G = 2;

// Server private key (hardcoded)
const PRIVATE_KEY = 52319;

// ESP public key (pre-computed: pow(2, 87321, 104729))
const PEER_PUBLIC_KEY = 63935;

function modPow(base: number, exp: number, mod: number): number {
  let result = 1;
  base = base % mod;
  while (exp > 0) {
    if (exp % 2 === 1) {
      result = (result * base) % mod;
    }
    exp = Math.floor(exp / 2);
    base = (base * base) % mod;
  }
  return result;
}

export function initCrypto(): { publicKey: number; aesKey: Buffer } {
  const publicKey = modPow(DH_G, PRIVATE_KEY, DH_P);
  const sharedSecret = modPow(PEER_PUBLIC_KEY, PRIVATE_KEY, DH_P);

  const aesKey = crypto.createHash("sha256").update(String(sharedSecret)).digest();

  console.log("DH public key:", publicKey);
  console.log("Shared secret establecido");

  return { publicKey, aesKey };
}

export function encryptValue(value: number | string, aesKey: Buffer): string {
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv("aes-256-cbc", aesKey, iv);
  let encrypted = cipher.update(String(value), "utf8", "hex");
  encrypted += cipher.final("hex");
  return iv.toString("hex") + ":" + encrypted;
}

export function decryptValue(encryptedStr: string, aesKey: Buffer): string {
  const [ivHex, ctHex] = encryptedStr.split(":");
  const iv = Buffer.from(ivHex, "hex");
  const decipher = crypto.createDecipheriv("aes-256-cbc", aesKey, iv);
  let decrypted = decipher.update(ctHex, "hex", "utf8");
  decrypted += decipher.final("utf8");
  return decrypted;
}
