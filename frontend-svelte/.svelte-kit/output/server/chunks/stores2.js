import { w as writable } from "./index.js";
const initialUser = null;
const user = writable(initialUser);
const authReady = writable(false);
export {
  authReady as a,
  user as u
};
