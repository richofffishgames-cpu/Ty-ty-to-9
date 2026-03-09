-- Insert test platforms
INSERT OR IGNORE INTO platforms (name, baseUrl, encryptedMasterCredentials, isActive) VALUES 
  ('GamingHub', 'https://gaminghub.example.com', 'encrypted_master_creds_1', 'active'),
  ('PlayZone', 'https://playzone.example.com', 'encrypted_master_creds_2', 'active'),
  ('GameMaster', 'https://gamemaster.example.com', 'encrypted_master_creds_3', 'active');

-- Insert test users (passwords would be encrypted in production)
INSERT OR IGNORE INTO users (openId, name, email, loginMethod, role, balance) VALUES 
  ('test_user_1', 'Alice Johnson', 'alice@example.com', 'oauth', 'user', '1.5'),
  ('test_user_2', 'Bob Smith', 'bob@example.com', 'oauth', 'user', '0.8'),
  ('test_user_3', 'Charlie Brown', 'charlie@example.com', 'oauth', 'admin', '5.0');

-- Insert test transactions
INSERT OR IGNORE INTO transactions (userId, type, amount, currency, status, invoiceId, createdAt) VALUES 
  (1, 'deposit', '1.0', 'BTC', 'confirmed', 'inv_001', datetime('now', '-2 days')),
  (1, 'deposit', '0.5', 'BTC', 'confirmed', 'inv_002', datetime('now', '-1 day')),
  (2, 'deposit', '0.8', 'BTC', 'confirmed', 'inv_003', datetime('now', '-3 days'));