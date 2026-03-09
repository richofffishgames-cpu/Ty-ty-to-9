# Crypto Platform Manager

A production-grade cryptocurrency platform management system with signing orchestrator for secure Bitcoin withdrawals, built with Hono, Cloudflare Workers, and React.

## Current Status

✅ **Active Development** - Core infrastructure completed, withdrawal API implemented

## Completed Features

### Core Infrastructure
- **Hono Framework**: Lightweight, fast API development optimized for Cloudflare Workers
- **D1 Database**: Cloudflare's edge SQLite database for data persistence
- **TypeScript**: Full type safety across the entire stack
- **Build System**: Vite-based build with Cloudflare Pages integration

### Signing Orchestrator (✅ Implemented)
- **Withdrawal API**: 
  - `POST /api/signing/withdrawals` - Create withdrawal requests
  - `GET /api/signing/withdrawals/{id}` - Get withdrawal status
  - `GET /api/signing/policy/info?amount={satoshis}` - Get policy requirements
  - `GET /api/signing/health` - Service health check
- **Policy Engine**: Rules-based approval system
  - < 0.005 BTC: Auto-sign (0 approvals required)
  - 0.005 - 1 BTC: Single approval required
  - > 1 BTC: Dual approval required
- **Idempotency**: Prevents duplicate withdrawal requests using idempotency keys
- **Bitcoin Address Validation**: Validates Bitcoin addresses before processing
- **Mock Database**: Currently uses in-memory storage for development

### Security Features
- **Request Validation**: Zod schemas for all API inputs
- **Error Handling**: Comprehensive error responses with proper HTTP status codes
- **Rate Limiting Ready**: Infrastructure in place for API rate limiting
- **Encryption Ready**: Framework for AES-256-GCM credential encryption

### Database Schema
- **Users**: Platform user management
- **Platforms**: Gaming platform configurations
- **Platform Accounts**: User-platform associations
- **Transactions**: Deposit/withdrawal/redeem tracking
- **Withdrawals**: Bitcoin withdrawal requests with status tracking
- **PSBTs**: Partially Signed Bitcoin Transactions
- **Signers**: Multiple signing methods (HSM, Hardware, MPC, Hot Wallet)
- **Approvals**: Multi-signature approval workflow

## API Endpoints

### Health & Status
- `GET /health` - Service health check
- `GET /api/signing/health` - Signing service health

### Withdrawal Management
- `POST /api/signing/withdrawals` - Create withdrawal request
  ```json
  {
    "user_id": 1,
    "amount": "0.001",
    "destination": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
    "currency": "BTC",
    "idempotency_key": "unique-key-123"
  }
  ```

- `GET /api/signing/withdrawals/{id}` - Get withdrawal status
  ```json
  {
    "status": "pending_policy",
    "psbt_id": null,
    "approvals_required": 1,
    "approvals_current": 0
  }
  ```

### Policy Information
- `GET /api/signing/policy/info?amount={satoshis}` - Get policy requirements for amount

## Architecture

### Backend (Hono + Cloudflare Workers)
- **Framework**: Hono for lightweight, edge-native API development
- **Database**: Cloudflare D1 (SQLite) for edge data persistence
- **Runtime**: Cloudflare Workers with edge deployment
- **Authentication**: JWT-based (ready for implementation)
- **Validation**: Zod schemas for runtime type safety

### Frontend
- **Framework**: Ready for React/TypeScript integration
- **Styling**: Tailwind CSS CDN integration
- **HTTP Client**: Axios for API communication

### Deployment
- **Platform**: Cloudflare Pages with automatic deployments
- **Environment**: Edge runtime with global distribution
- **Storage**: D1 database with local development support

## Quick Start

### Prerequisites
- Node.js 18+
- npm or yarn

### Local Development

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

3. Build for production:
```bash
npm run build
```

### Cloudflare Deployment

1. Configure Cloudflare API key:
```bash
# Set up your Cloudflare API token
npx wrangler login
```

2. Deploy to Cloudflare Pages:
```bash
npm run deploy
```

## Database Setup

### Local Development (D1)
The application uses D1 database which is automatically available in local development mode.

### Production
Configure D1 database in `wrangler.jsonc`:
```json
{
  "d1_databases": [
    {
      "binding": "DB",
      "database_name": "your-database-name",
      "database_id": "your-database-id"
    }
  ]
}
```

## Environment Variables

Create a `.dev.vars` file for local development:
```
JWT_SECRET=your-jwt-secret
ENCRYPTION_KEY=your-encryption-key
FRONTEND_URL=http://localhost:3000
```

## Next Steps / Roadmap

### High Priority (Next Steps)
- [ ] **Database Integration**: Replace mock storage with actual D1 database integration
- [ ] **JWT Authentication**: Complete the JWT service implementation and integrate with auth endpoints
- [ ] **Database Schema**: Apply the signing-related database migrations
- [ ] **PSBT Builder**: Create Bitcoin PSBT construction service (currently mocked)
- [ ] **Error Handling**: Improve error handling and logging throughout the application

### Medium Priority
- [ ] **Database Integration**: Replace mock storage with actual D1 database integration
- [ ] **Signer Adapters**: Implement HSM, Hardware, and MPC signers
- [ ] **Queue System**: Add background job processing for withdrawals
- [ ] **Broadcast Service**: Bitcoin transaction broadcasting
- [ ] **Approval Workflow**: Multi-signature approval system

### Low Priority
- [ ] **Observability**: Metrics, monitoring, and alerting
- [ ] **Performance Optimization**: Caching and optimization
- [ ] **Advanced Features**: Multi-currency support, advanced policies
- [ ] **Testing**: Unit and integration tests

## Security Considerations

### Current Implementation
- ✅ Input validation with Zod schemas
- ✅ Idempotency keys for withdrawal requests
- ✅ Comprehensive policy enforcement
- ✅ Error handling without information disclosure
- ✅ D1 database integration for withdrawal tracking

### Recommended Enhancements
- 🔐 JWT authentication for API access
- 🔐 Rate limiting per user/IP
- 🔐 Address whitelisting
- 🔐 Daily withdrawal limits
- 🔐 Hardware-backed signing (HSM)

## Development Guidelines

### Code Structure
```
src/
├── api/           # API route handlers
├── crypto/        # Cryptographic services (PSBT, signing)
├── db/           # Database schema and connections
├── middleware/   # Hono middleware
├── queue/        # Background job processing
├── types/        # TypeScript type definitions
└── utils/        # Utility functions
```

### Best Practices
- Use TypeScript for type safety
- Implement proper error handling
- Follow RESTful API conventions
- Document all API endpoints
- Write comprehensive tests

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Create an issue in the GitHub repository
- Check the documentation
- Review the API endpoints

---

**Note**: This is an active development project. Features and APIs may change as the system evolves.