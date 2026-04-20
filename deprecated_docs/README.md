# 📚 Deprecated Documentation

This folder contains development notes, process documentation, and reference materials that were used during development but are not needed for production deployment.

## Contents

### Phase Documentation
- `PHASE1_*.md` - Phase 1 implementation notes
- `PHASE_2A_*.md` - Phase 2A AI Chat implementation
- `PHASE_2B_*.md` - Phase 2B Fine-tuning notes
- `PHASE4_PLAN.md` - Phase 4 planning

### Feature Documentation
- Implementation guides for features that are already in production
- API documentation for completed features
- Integration guides for implemented systems

### Deployment Guides (Reference)
- Multiple deployment documents from different phases
- Some may have conflicting information (refer to root `DEPLOYMENT.md` instead)

### Development References
- Algorithm analysis
- Architecture analysis
- Integration references
- Testing documentation

## How to Use

**For Production:**
- Refer to root directory `DEPLOYMENT.md`, `docker-compose.yml`, `nginx.conf`
- Check `PRODUCTION_CLEANUP_PLAN.md` for deployment checklist

**For Development Reference:**
- Browse this folder for background context
- Useful for understanding architecture decisions
- Reference for debugging specific features

## Why Archived?

These files were moved here to:
1. ✅ Keep root directory clean and deployment-focused
2. ✅ Reduce git repository size
3. ✅ Prevent deployment confusion (too many docs)
4. ✅ Maintain historical context (not deleted)

**Generated:** 2026-04-20  
**Cleanup:** Production-ready separation
