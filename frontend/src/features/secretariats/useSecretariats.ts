import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";

/** Charge les secrétariats de l'utilisateur et expose le secrétariat courant. */
export function useSecretariats() {
  const requete = useQuery({
    queryKey: ["secretariats"],
    queryFn: api.listerSecretariats,
  });
  const secretariat = requete.data?.[0] ?? null;
  return { ...requete, secretariat };
}
