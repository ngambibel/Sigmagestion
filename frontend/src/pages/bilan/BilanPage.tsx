import { EnTetePage, EtatVide } from "../../components/layout/EnTetePage";

export default function BilanPage() {
  return (
    <div>
      <EnTetePage titre="Bilan" sousTitre="Votre chiffre d'affaires et vos indicateurs." />
      <EtatVide message="Le tableau de bord et les rapports arrivent à une phase ultérieure." />
    </div>
  );
}
