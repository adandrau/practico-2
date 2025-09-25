import { Router } from 'express';
import jwt from 'jsonwebtoken';
import AuthService from '../services/authService';

const router = Router();

router.get('/', (_req, res) => res.json({ ok: true }));

router.post('/login', async (req, res) => {
  try {
    const { username, email, password } = req.body;
    const identifier = (username ?? email ?? '').toString().trim();

    if (!identifier || !password) {
      return res.status(400).json({ message: 'username/email and password required' });
    }

    const user = await AuthService.authenticate(identifier, password);

    const token = jwt.sign(
      { sub: user.id, username: user.username },
      process.env.JWT_SECRET || 'dev_secret',
      { expiresIn: '1h' }
    );

    return res.json({ token });
  } catch (e: any) {
    return res.status(401).json({ message: e.message || 'Login failed' });
  }
});

router.post('/forgot-password', (_req, res) => res.status(501).json({ message: 'Not implemented' }));
router.post('/reset-password',  (_req, res) => res.status(501).json({ message: 'Not implemented' }));
router.post('/set-password',    (_req, res) => res.status(501).json({ message: 'Not implemented' }));

export default router;
