"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import {
  onAuthStateChanged,
  signInWithPopup,
  signOut as firebaseSignOut,
  type User,
} from "firebase/auth";
import {
  doc,
  getDoc,
  setDoc,
  updateDoc,
  collection,
  query,
  where,
  getDocs,
  increment,
  serverTimestamp,
} from "firebase/firestore";
import { auth, db, googleProvider } from "./firebase";

export type UserRole = "cliente" | "admin";

export interface UserProfile {
  uid: string;
  email: string;
  nome: string;
  sobrenome: string;
  telefone: string | null;
  fotoURL: string | null;
  role: UserRole;
  saldoCreditos: number;
  totalConsultas: number;
  codigoIndicacao: string;
  createdAt: string;
  perfilCompleto: boolean;
  onboardingCompleto: boolean;
}

interface AuthContextType {
  user: User | null;
  profile: UserProfile | null;
  loading: boolean;
  loginWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({} as AuthContextType);

/** Gera um código de indicação único baseado no UID */
function gerarCodigoIndicacao(uid: string): string {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  let code = "";
  for (let i = 0; i < 6; i++) {
    code += chars[uid.charCodeAt(i % uid.length) % chars.length];
  }
  return code;
}

/** Processa um código de indicação: +2 CR para referenciador e +2 CR para novo usuário */
export async function processarIndicacao(
  novoUid: string,
  codigoUsado: string
): Promise<boolean> {
  try {
    const q = query(
      collection(db, "users"),
      where("codigoIndicacao", "==", codigoUsado.toUpperCase())
    );
    const snap = await getDocs(q);
    if (snap.empty) return false;

    const referenciador = snap.docs[0];
    if (referenciador.id === novoUid) return false; // não pode indicar a si mesmo

    // +2 CR para quem indicou
    await updateDoc(doc(db, "users", referenciador.id), {
      saldoCreditos: increment(2),
    });

    // +2 CR para o novo usuário (além dos 2 iniciais)
    await updateDoc(doc(db, "users", novoUid), {
      saldoCreditos: increment(2),
      indicadoPor: referenciador.id,
    });

    return true;
  } catch {
    return false;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchProfile = useCallback(async (uid: string) => {
    try {
      const snap = await getDoc(doc(db, "users", uid));
      if (snap.exists()) {
        setProfile(snap.data() as UserProfile);
      } else {
        setProfile(null);
      }
    } catch {
      setProfile(null);
    }
  }, []);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      setUser(firebaseUser);
      if (firebaseUser) {
        await fetchProfile(firebaseUser.uid);
      } else {
        setProfile(null);
      }
      setLoading(false);
    });
    return unsubscribe;
  }, [fetchProfile]);

  const loginWithGoogle = useCallback(async () => {
    try {
      const result = await signInWithPopup(auth, googleProvider);
      const uid = result.user.uid;

      const existing = await getDoc(doc(db, "users", uid));
      if (!existing.exists()) {
        const codigoIndicacao = gerarCodigoIndicacao(uid);
        await setDoc(doc(db, "users", uid), {
          uid,
          email: result.user.email || "",
          nome: result.user.displayName?.split(" ")[0] || "",
          sobrenome: result.user.displayName?.split(" ").slice(1).join(" ") || "",
          telefone: null,
          fotoURL: result.user.photoURL || null,
          role: "cliente",
          saldoCreditos: 2, // 2 créditos grátis no cadastro
          totalConsultas: 0,
          codigoIndicacao,
          createdAt: serverTimestamp(),
          updatedAt: serverTimestamp(),
          perfilCompleto: false,
          onboardingCompleto: false,
        });
      }
      await fetchProfile(uid);
    } catch (error: any) {
      if (error.code !== "auth/popup-closed-by-user") {
        throw error;
      }
    }
  }, [fetchProfile]);

  const logout = useCallback(async () => {
    await firebaseSignOut(auth);
    setUser(null);
    setProfile(null);
  }, []);

  const refreshProfile = useCallback(async () => {
    if (user) await fetchProfile(user.uid);
  }, [user, fetchProfile]);

  return (
    <AuthContext.Provider
      value={{ user, profile, loading, loginWithGoogle, logout, refreshProfile }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx.loginWithGoogle) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
