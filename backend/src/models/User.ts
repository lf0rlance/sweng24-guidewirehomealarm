import mongoose, { Schema, Document } from "mongoose";

interface IUser extends Document {
  googleId: string;
  email: string;
  name: string;
}

const UserSchema: Schema = new Schema({
  googleId: { type: String, required: true, unique: true },
  email: { type: String, required: true },
  name: { type: String, required: true },
});

export default mongoose.model<IUser>("User", UserSchema);
