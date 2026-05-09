import crypto from "crypto";

// Diffie-Hellman parameters
const DH_P = 104729;
const DH_G = 2;

// Server private key
const PRIVATE_KEY = 52319;

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

export function getPublicKey(): number {
  return modPow(DH_G, PRIVATE_KEY, DH_P);
}

export function computeSharedSecret(peerPublicKey: number): Buffer {
  const shared = modPow(peerPublicKey, PRIVATE_KEY, DH_P);
  return crypto.createHash("sha256").update(String(shared)).digest();
}

export function encrypt(
  plaintext: string,
  aesKey: Buffer
): { ciphertext: string; tag: string; nonce: string } {
  const nonce = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv("aes-256-cbc", aesKey, nonce);
  let ciphertext = cipher.update(plaintext, "utf8", "hex");
  ciphertext += cipher.final("hex");

  const tag = crypto
    .createHmac("sha256", aesKey)
    .update(Buffer.concat([nonce, Buffer.from(ciphertext, "hex")]))
    .digest("hex");

  return { ciphertext, tag, nonce: nonce.toString("hex") };
}

export function decrypt(
  ciphertext: string,
  tag: string,
  nonce: string,
  aesKey: Buffer
): string {
  const nonceBuffer = Buffer.from(nonce, "hex");
  const ciphertextBuffer = Buffer.from(ciphertext, "hex");

  const expectedTag = crypto
    .createHmac("sha256", aesKey)
    .update(Buffer.concat([nonceBuffer, ciphertextBuffer]))
    .digest("hex");

  if (tag !== expectedTag) {
    throw new Error("Tag verification failed");
  }

  const decipher = crypto.createDecipheriv("aes-256-cbc", aesKey, nonceBuffer);
  let decrypted = decipher.update(ciphertext, "hex", "utf8");
  decrypted += decipher.final("utf8");
  return decrypted;
}
