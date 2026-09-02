import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { api, ApiError } from "../../lib/api";
import { useAuthStore } from "../../stores/auth";

const schema = z.object({
  nom: z.string().min(2, "Indiquez votre nom complet."),
  telephone: z
    .string()
    .regex(/^[+\d][\d\s.-]{7,}$/, "Numéro invalide. Ex. +237 6XX XXX XXX."),
  email: z.string().email("Adresse e-mail invalide.").or(z.literal("")).optional(),
  password: z.string().min(8, "Au moins 8 caractères."),
});

type Champs = z.infer<typeof schema>;

export function RegisterForm({ onBascule }: { onBascule: () => void }) {
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<Champs>({ resolver: zodResolver(schema) });

  const definirSession = useAuthStore((s) => s.definirSession);
  const definirUtilisateur = useAuthStore((s) => s.definirUtilisateur);

  const inscription = useMutation({
    mutationFn: async (champs: Champs) => {
      const r = await api.inscription({
        nom: champs.nom,
        telephone: champs.telephone,
        email: champs.email || undefined,
        password: champs.password,
      });
      definirSession(r.access, r.refresh);
      definirUtilisateur(await api.moi());
    },
    onError: (erreur) => {
      // Remonte les erreurs de champ renvoyées par le backend.
      if (erreur instanceof ApiError && erreur.corps && typeof erreur.corps === "object") {
        for (const [champ, messages] of Object.entries(erreur.corps as Record<string, string[]>)) {
          if (champ in schema.shape) {
            setError(champ as keyof Champs, {
              message: Array.isArray(messages) ? messages.join(" ") : String(messages),
            });
          }
        }
      }
    },
  });

  const erreurGlobale =
    inscription.error && !(inscription.error instanceof ApiError)
      ? "Inscription impossible. Vérifiez que le backend est démarré."
      : undefined;

  return (
    <div className="mx-auto flex min-h-screen max-w-sm flex-col justify-center px-5 py-8">
      <h1 className="mb-1 text-3xl">Créer un compte</h1>
      <p className="mb-8 text-encre-douce">Ouvrez votre secrétariat en quelques secondes.</p>

      <form onSubmit={handleSubmit((c) => inscription.mutate(c))} className="flex flex-col gap-4">
        <Input label="Nom complet" placeholder="Jean Dupont" erreur={errors.nom?.message} {...register("nom")} />
        <Input
          label="Téléphone"
          placeholder="+237 6XX XXX XXX"
          inputMode="tel"
          erreur={errors.telephone?.message}
          {...register("telephone")}
        />
        <Input
          label="E-mail (facultatif)"
          type="email"
          placeholder="vous@exemple.cm"
          erreur={errors.email?.message}
          {...register("email")}
        />
        <Input
          label="Mot de passe"
          type="password"
          placeholder="••••••••"
          autoComplete="new-password"
          erreur={errors.password?.message}
          {...register("password")}
        />
        {erreurGlobale && <p className="text-sm text-magenta">{erreurGlobale}</p>}
        <Button type="submit" taille="grand" disabled={inscription.isPending} className="mt-2">
          {inscription.isPending ? "Création…" : "Créer mon compte"}
        </Button>
      </form>

      <p className="mt-6 text-center text-encre-douce">
        Déjà un compte ?{" "}
        <button onClick={onBascule} className="font-medium text-cyan underline">
          Se connecter
        </button>
      </p>
    </div>
  );
}
