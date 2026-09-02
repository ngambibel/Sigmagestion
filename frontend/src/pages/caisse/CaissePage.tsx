import { EnTetePage, EtatVide } from "../../components/layout/EnTetePage";

export default function CaissePage() {
  return (
    <div>
      <EnTetePage titre="Caisse" sousTitre="Enregistrez vos prestations et encaissez." />
      <EtatVide message="Le point de vente arrive à la phase suivante. Ici, vous saisirez les prestations et encaisserez." />
    </div>
  );
}
