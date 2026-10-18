/**
 * Client API typé pour SigmaGestion.
 * Injecte le token d'accès, rafraîchit automatiquement sur 401 une fois.
 */
import { useAuthStore, type Utilisateur } from "../stores/auth";

export const BASE_URL =
  import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  constructor(
    public statut: number,
    public corps: unknown,
  ) {
    super(`Erreur API ${statut}`);
    this.name = "ApiError";
  }
}

interface Options extends RequestInit {
  /** Requête publique : n'ajoute pas le header d'autorisation. */
  publique?: boolean;
  /** Interne : empêche une seconde tentative de refresh. */
  _reessaye?: boolean;
}

async function rafraichirAcces(): Promise<boolean> {
  const { refreshToken, definirAcces, reinitialiser } = useAuthStore.getState();
  if (!refreshToken) return false;
  const reponse = await fetch(`${BASE_URL}/auth/rafraichir/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: refreshToken }),
  });
  if (!reponse.ok) {
    reinitialiser();
    return false;
  }
  const corps = (await reponse.json()) as { access: string };
  definirAcces(corps.access);
  return true;
}

async function requete<T>(chemin: string, options: Options = {}): Promise<T> {
  const { publique, _reessaye, headers, ...reste } = options;
  const token = useAuthStore.getState().accessToken;
  const entetes: Record<string, string> = { ...(headers as Record<string, string>) };
  // Pour un envoi FormData, on laisse le navigateur fixer le Content-Type (frontière multipart).
  if (!(reste.body instanceof FormData)) {
    entetes["Content-Type"] = "application/json";
  }
  if (!publique && token) entetes.Authorization = `Bearer ${token}`;

  const reponse = await fetch(`${BASE_URL}${chemin}`, { headers: entetes, ...reste });

  // 401 → tentative unique de rafraîchissement puis nouvel essai.
  if (reponse.status === 401 && !publique && !_reessaye) {
    if (await rafraichirAcces()) {
      return requete<T>(chemin, { ...options, _reessaye: true });
    }
  }

  const corps =
    reponse.status === 204 || reponse.status === 205
      ? null
      : await reponse.json().catch(() => null);
  if (!reponse.ok) throw new ApiError(reponse.status, corps);
  return corps as T;
}

export interface Sante {
  base: string;
  redis: string;
}

export interface ReponseConnexion {
  access: string;
  refresh: string;
  role: string;
  nom: string;
  doit_changer_mdp: boolean;
}

export interface DonneesInscription {
  nom: string;
  telephone: string;
  email?: string;
  password: string;
}

export interface Secretariat {
  id: number;
  nom: string;
  code: string;
  ville: string;
  quartier: string;
  telephone: string;
  devise: string;
  onboarding_termine: boolean;
  proprietaire: number;
  cree_le: string;
}

export interface PlageHoraire {
  jour: number; // 0 = lundi … 6 = dimanche
  jour_libelle: string;
  ouvert: boolean;
  heure_debut: string; // "HH:MM:SS"
  heure_fin: string;
}

export interface ParametreNotification {
  intervalle_ca_min: number;
  alerte_ca_on: boolean;
  alerte_stock_on: boolean;
  bilan_jour_on: boolean;
  alerte_ecart_caisse_on: boolean;
  alerte_annulation_on: boolean;
  alerte_session_on: boolean;
  ne_pas_deranger: boolean;
  seuil_ecart_caisse: number;
  dernier_envoi_ca: string | null;
  dernier_bilan_jour: string | null;
}

export interface Notification {
  id: number;
  type: string;
  type_libelle: string;
  titre: string;
  corps: string;
  url: string;
  lu: boolean;
  archivee: boolean;
  cree_le: string;
}

export interface ListeNotifications {
  resultats: Notification[];
  non_lues: number;
}

export interface ServiceModele {
  nom: string;
  categorie: string;
  unite_facturation: string;
  prix: number;
  consomme_stock: boolean;
}

export interface ConsommableModele {
  nom: string;
  unite_mesure: string;
  prix_achat: number;
  seuil_alerte: number;
}

export interface ModelesOnboarding {
  services: ServiceModele[];
  consommables: ConsommableModele[];
}

export interface Service {
  id: number;
  nom: string;
  categorie: string;
  unite_facturation: string;
  prix: number;
  consomme_stock: boolean;
  actif: boolean;
  couleur: string;
  icone: string;
  image: string | null;
  ordre: number;
  activable: boolean;
  recto_verso_possible: boolean;
}

export interface NomenclatureLigne {
  id: number;
  consommable: number;
  consommable_nom: string;
  unite_mesure: string;
  qte_par_unite: string;
  divise_en_recto_verso: boolean;
}

export interface Consommable {
  id: number;
  nom: string;
  unite_mesure: string;
  prix_achat: number;
  qte_stock: string;
  seuil_alerte: string;
  seuil_critique: string | null;
  fournisseur: string;
  actif: boolean;
  sous_seuil: boolean;
}

export interface SessionCaisse {
  id: number;
  employe: number;
  employe_nom: string;
  fond_initial: number;
  statut: string;
  montant_theorique: number | null;
  montant_compte: number | null;
  ecart: number | null;
  commentaire: string;
  ouverte_le: string;
  cloturee_le: string | null;
  montant_theorique_estime?: number;
}

export interface Depense {
  id: number;
  categorie: string;
  categorie_libelle: string;
  montant: number;
  description: string;
  justificatif: string | null;
  auteur_nom: string;
  cree_le: string;
}

export interface LignePrestation {
  id: number;
  service: number;
  nom_service: string;
  prix_unitaire: number;
  prix_catalogue: number;
  quantite: number;
  cout_unitaire: number;
  recto_verso: boolean;
  montant: number;
}

export interface Prestation {
  id: number;
  numero: string;
  statut: string;
  mode_paiement: string;
  nom_client: string;
  remise: number;
  montant_total: number;
  montant_recu: number | null;
  monnaie_rendue: number | null;
  employe_nom: string;
  lignes: LignePrestation[];
  cree_le: string;
}

export interface ResultatEncaissement {
  prestation: Prestation;
  alertes_stock: Consommable[];
  /** Vrai si la vente a été mise en file hors ligne (pas encore synchronisée). */
  hors_ligne?: boolean;
}

export interface SaisieLigne {
  service: number;
  quantite: number;
  prix_unitaire?: number;
  recto_verso?: boolean;
}

export interface TableauDeBord {
  ca_jour: number;
  ca_veille: number;
  variation_pct: number | null;
  nb_prestations_jour: number;
  marge_jour: number;
  serie_30j: { date: string; ca: number }[];
  par_service: { nom_service: string; ca: number }[];
  top_services: { nom_service: string; ca: number }[];
  par_employe: { employe: string; ca: number; nb: number }[];
  consommables_sous_seuil: {
    id: number;
    nom: string;
    qte_stock: string;
    seuil_alerte: string;
    unite_mesure: string;
  }[];
}

export interface TableauDeBordEmploye {
  session: {
    id: number;
    fond_initial: number;
    ouverte_le: string;
    total_encaisse: number;
    nb_prestations: number;
    especes: number;
    momo: number;
    orange: number;
    credit: number;
    montant_theorique_estime: number;
  } | null;
  mes_prestations: {
    id: number;
    numero: string;
    montant_total: number;
    mode_paiement: string;
    statut: string;
    cree_le: string;
  }[];
  consommables_sous_seuil: {
    id: number;
    nom: string;
    qte_stock: string;
    seuil_alerte: string;
    unite_mesure: string;
  }[];
}

export interface Rapport {
  titre: string;
  colonnes: { cle: string; libelle: string }[];
  lignes: Record<string, string | number>[];
  totaux: Record<string, number | Record<string, number>>;
}

export type TypeRapport = "ventes" | "rentabilite" | "stock" | "caisse";

/** Télécharge un rapport en CSV (fetch authentifié → blob → déclenchement du téléchargement). */
export async function telechargerRapportCsv(type: TypeRapport, params: string, nomFichier: string) {
  const token = useAuthStore.getState().accessToken;
  const sep = params ? "&" : "";
  const reponse = await fetch(`${BASE_URL}/rapports/${type}/?export=csv${sep}${params}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!reponse.ok) throw new ApiError(reponse.status, null);
  const blob = await reponse.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${nomFichier}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export interface Employe {
  id: number;
  nom: string;
  telephone: string;
  role: string;
  role_libelle: string;
  is_active: boolean;
  doit_changer_mdp: boolean;
  date_joined: string;
}

export interface EmployeCree extends Employe {
  mot_de_passe_provisoire: string;
}

export interface ActiviteEmploye {
  employe: Employe;
  ca_genere: number;
  nb_prestations: number;
  nb_annulations: number;
  nb_sessions: number;
  ecart_cumule: number;
  nb_sessions_avec_ecart: number;
}

export interface Client {
  id: number;
  nom: string;
  telephone: string;
  type: string;
  type_libelle: string;
  plafond_credit: number;
  encours: number;
  actif: boolean;
  cree_le: string;
}

export interface Reglement {
  id: number;
  montant: number;
  commentaire: string;
  auteur_nom: string;
  cree_le: string;
}

export interface HistoriqueClient {
  client: Client;
  prestations: Prestation[];
  reglements: Reglement[];
  credits_non_regles: number;
}

export interface MouvementStock {
  id: number;
  consommable: number;
  consommable_nom: string;
  type: string;
  type_libelle: string;
  quantite: string;
  stock_avant: string;
  stock_apres: string;
  prix_achat_unitaire: number | null;
  motif: string;
  auteur_nom: string;
  cree_le: string;
}

export const api = {
  sante: () => requete<Sante>("/sante/", { publique: true }),

  connexion: (telephone: string, password: string) =>
    requete<ReponseConnexion>("/auth/connexion/", {
      method: "POST",
      publique: true,
      body: JSON.stringify({ telephone, password }),
    }),

  inscription: (donnees: DonneesInscription) =>
    requete<ReponseConnexion>("/auth/inscription/", {
      method: "POST",
      publique: true,
      body: JSON.stringify(donnees),
    }),

  moi: () => requete<Utilisateur>("/moi/"),

  changerMotDePasse: (nouveau_mot_de_passe: string) =>
    requete<{ detail: string }>("/moi/changer-mot-de-passe/", {
      method: "POST",
      body: JSON.stringify({ nouveau_mot_de_passe }),
    }),

  // --- Employés ---
  listerEmployes: () => requete<Employe[]>("/employes/"),
  creerEmploye: (donnees: { nom: string; telephone: string; role: string }) =>
    requete<EmployeCree>("/employes/", { method: "POST", body: JSON.stringify(donnees) }),
  desactiverEmploye: (id: number) =>
    requete<Employe>(`/employes/${id}/desactiver/`, { method: "POST", body: "{}" }),
  reactiverEmploye: (id: number) =>
    requete<Employe>(`/employes/${id}/reactiver/`, { method: "POST", body: "{}" }),
  activiteEmploye: (id: number) => requete<ActiviteEmploye>(`/employes/${id}/activite/`),

  deconnexion: (refresh: string) =>
    requete<null>("/auth/deconnexion/", {
      method: "POST",
      body: JSON.stringify({ refresh }),
    }),

  // --- Secrétariats ---
  listerSecretariats: () => requete<Secretariat[]>("/secretariats/"),

  creerSecretariat: (donnees: Partial<Secretariat>) =>
    requete<Secretariat>("/secretariats/", {
      method: "POST",
      body: JSON.stringify(donnees),
    }),

  modifierSecretariat: (id: number, donnees: Partial<Secretariat>) =>
    requete<Secretariat>(`/secretariats/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(donnees),
    }),

  // --- Plages horaires et paramètres de notification ---
  getPlagesHoraires: (secretariatId: number) =>
    requete<PlageHoraire[]>(`/secretariats/${secretariatId}/plages-horaires/`),
  putPlagesHoraires: (
    secretariatId: number,
    plages: { jour: number; ouvert: boolean; heure_debut: string; heure_fin: string }[],
  ) =>
    requete<PlageHoraire[]>(`/secretariats/${secretariatId}/plages-horaires/`, {
      method: "PUT",
      body: JSON.stringify(plages),
    }),
  getParametresNotification: (secretariatId: number) =>
    requete<ParametreNotification>(`/secretariats/${secretariatId}/parametres-notification/`),
  patchParametresNotification: (
    secretariatId: number,
    donnees: Partial<ParametreNotification>,
  ) =>
    requete<ParametreNotification>(`/secretariats/${secretariatId}/parametres-notification/`, {
      method: "PATCH",
      body: JSON.stringify(donnees),
    }),

  // --- Onboarding ---
  modelesOnboarding: () => requete<ModelesOnboarding>("/onboarding/modeles/"),

  // --- Catalogue ---
  listerServices: () => requete<Service[]>("/services/"),
  creerService: (donnees: Partial<Service> | FormData) =>
    requete<Service>("/services/", {
      method: "POST",
      body: donnees instanceof FormData ? donnees : JSON.stringify(donnees),
    }),
  modifierService: (id: number, donnees: Partial<Service> | FormData) =>
    requete<Service>(`/services/${id}/`, {
      method: "PATCH",
      body: donnees instanceof FormData ? donnees : JSON.stringify(donnees),
    }),
  supprimerService: (id: number) =>
    requete<null>(`/services/${id}/`, { method: "DELETE" }),
  getNomenclature: (serviceId: number) =>
    requete<NomenclatureLigne[]>(`/services/${serviceId}/nomenclature/`),
  putNomenclature: (
    serviceId: number,
    lignes: { consommable: number; qte_par_unite: number; divise_en_recto_verso?: boolean }[],
  ) =>
    requete<NomenclatureLigne[]>(`/services/${serviceId}/nomenclature/`, {
      method: "PUT",
      body: JSON.stringify(lignes),
    }),

  // --- Stocks ---
  listerConsommables: () => requete<Consommable[]>("/consommables/"),
  creerConsommable: (donnees: Record<string, unknown>) =>
    requete<Consommable>("/consommables/", {
      method: "POST",
      body: JSON.stringify(donnees),
    }),
  modifierConsommable: (id: number, donnees: Record<string, unknown>) =>
    requete<Consommable>(`/consommables/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(donnees),
    }),
  supprimerConsommable: (id: number) =>
    requete<null>(`/consommables/${id}/`, { method: "DELETE" }),
  entreeStock: (
    id: number,
    donnees: { quantite: number; prix_total_lot: number; fournisseur?: string; motif?: string },
  ) =>
    requete<{ mouvement: unknown; consommable: Consommable }>(
      `/consommables/${id}/entree-stock/`,
      { method: "POST", body: JSON.stringify(donnees) },
    ),
  ajustementStock: (id: number, donnees: { quantite_delta: number; motif: string }) =>
    requete<{ mouvement: unknown; consommable: Consommable }>(
      `/consommables/${id}/ajustement/`,
      { method: "POST", body: JSON.stringify(donnees) },
    ),

  // --- Sessions de caisse ---
  sessionActive: () => requete<SessionCaisse | null>("/sessions-caisse/active/"),
  ouvrirSession: (fond_initial: number) =>
    requete<SessionCaisse>("/sessions-caisse/", {
      method: "POST",
      body: JSON.stringify({ fond_initial }),
    }),
  cloturerSession: (id: number, donnees: { montant_compte: number; commentaire: string }) =>
    requete<SessionCaisse>(`/sessions-caisse/${id}/cloturer/`, {
      method: "POST",
      body: JSON.stringify(donnees),
    }),

  // --- Dépenses ---
  listerDepenses: () => requete<Depense[]>("/depenses/"),
  creerDepense: (donnees: FormData) =>
    requete<Depense>("/depenses/", { method: "POST", body: donnees }),

  // --- Ventes / encaissement ---
  enregistrerPrestation: (payload: {
    lignes: SaisieLigne[];
    mode_paiement: string;
    remise: number;
    montant_recu?: number | null;
    nom_client?: string;
    client?: number | null;
    client_uuid?: string;
  }) =>
    requete<ResultatEncaissement>("/prestations/", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  listerPrestations: () => requete<Prestation[]>("/prestations/"),

  synchroniserPrestations: (ventes: unknown[]) =>
    requete<{ resultats: { client_uuid: string; statut: "ok" | "doublon" | "erreur"; detail?: string }[] }>(
      "/prestations/synchroniser/",
      { method: "POST", body: JSON.stringify({ ventes }) },
    ),
  annulerPrestation: (id: number, motif: string) =>
    requete<Prestation>(`/prestations/${id}/annuler/`, {
      method: "POST",
      body: JSON.stringify({ motif }),
    }),

  // --- Notifications push ---
  clePubliquePush: () => requete<{ cle_publique: string }>("/push/cle-publique/"),
  abonnerPush: (abonnement: { endpoint: string; keys: { p256dh: string; auth: string }; navigateur?: string }) =>
    requete<{ id: number }>("/push/abonnement/", {
      method: "POST",
      body: JSON.stringify(abonnement),
    }),
  desabonnerPush: (endpoint: string) =>
    requete<null>("/push/abonnement/", { method: "DELETE", body: JSON.stringify({ endpoint }) }),
  envoyerPushTest: () =>
    requete<{ envoyees: number }>("/push/test/", { method: "POST", body: "{}" }),

  // --- Centre de notifications ---
  listerNotifications: (archivees?: "seules" | "1") => {
    const suffixe = archivees ? `?archivees=${archivees}` : "";
    return requete<ListeNotifications>(`/notifications/${suffixe}`);
  },
  compteurNotifications: () =>
    requete<{ non_lues: number }>("/notifications/compteur/"),
  toutLireNotifications: () =>
    requete<{ marquees: number }>("/notifications/tout-lire/", { method: "POST", body: "{}" }),
  lireNotification: (id: number) =>
    requete<Notification>(`/notifications/${id}/lire/`, { method: "POST", body: "{}" }),
  archiverNotification: (id: number) =>
    requete<Notification>(`/notifications/${id}/archiver/`, { method: "POST", body: "{}" }),

  // --- Tableau de bord ---
  tableauDeBord: () => requete<TableauDeBord>("/tableau-de-bord/"),
  tableauDeBordEmploye: () => requete<TableauDeBordEmploye>("/tableau-de-bord/employe/"),

  // --- Rapports ---
  getRapport: (type: TypeRapport, params: string) =>
    requete<Rapport>(`/rapports/${type}/${params ? `?${params}` : ""}`),

  // --- Clients et créances ---
  listerClients: () => requete<Client[]>("/clients/"),
  creerClient: (donnees: {
    nom: string;
    telephone?: string;
    type?: string;
    plafond_credit?: number;
  }) => requete<Client>("/clients/", { method: "POST", body: JSON.stringify(donnees) }),
  modifierClient: (id: number, donnees: Partial<Client>) =>
    requete<Client>(`/clients/${id}/`, { method: "PATCH", body: JSON.stringify(donnees) }),
  reglementClient: (id: number, montant: number, commentaire = "") =>
    requete<{ reglement: Reglement; client: Client }>(`/clients/${id}/reglement/`, {
      method: "POST",
      body: JSON.stringify({ montant, commentaire }),
    }),
  historiqueClient: (id: number) => requete<HistoriqueClient>(`/clients/${id}/historique/`),

  // --- Journal des mouvements ---
  listerMouvements: (filtres?: { consommable?: number; type?: string }) => {
    const params = new URLSearchParams();
    if (filtres?.consommable) params.set("consommable", String(filtres.consommable));
    if (filtres?.type) params.set("type", filtres.type);
    const suffixe = params.toString() ? `?${params}` : "";
    return requete<MouvementStock[]>(`/mouvements-stock/${suffixe}`);
  },
};
