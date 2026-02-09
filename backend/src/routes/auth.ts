import express from "express";
import { OAuth2Client } from "google-auth-library";
import jwt from "jsonwebtoken";
import User from "../models/User"; // Mongoose user model
import dotenv from "dotenv";

dotenv.config();

const router = express.Router();
const client = new OAuth2Client(process.env.GOOGLE_CLIENT_ID);



router.post("/google", async (req, res) => {

  console.log("/auth/google route hit!");
  console.log("Body received:", req.body);

  const { idToken } = req.body;

  if (!idToken) {
    console.log("Missing idToken");
    return res.status(400).json({ error: "Missing idToken" });
  }

  if (!idToken) return res.status(400).json({ error: "Missing idToken" });

  try {
    // Verify token with Google
    const ticket = await client.verifyIdToken({
      idToken,
      audience: process.env.GOOGLE_CLIENT_ID,
    });

    const payload = ticket.getPayload();
    if (!payload || !payload.sub) {
      return res.status(401).json({ error: "Invalid Google token" });
    }

    const googleId = payload.sub;
    const email = payload.email;
    const name = payload.name;

    // Find or create user in MongoDB
    let user = await User.findOne({ googleId });
    if (!user) {
      user = new User({ googleId, email, name });
      await user.save();
    }

    // Create JWT for your app
    const token = jwt.sign(
      { userId: user._id, email: user.email },
      process.env.JWT_SECRET!,
      { expiresIn: "7d" }
    );

    // Return JWT to app
    res.json({ token, user: { id: user._id, email: user.email, name: user.name } });
  } catch (err) {
    console.error("Google token verification failed:", err);
    res.status(401).json({ error: "Invalid Google token" });
  }
});

export default router;
