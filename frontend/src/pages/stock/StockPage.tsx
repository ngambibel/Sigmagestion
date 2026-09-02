import { EnTetePage, EtatVide } from "../../components/layout/EnTetePage";

export default function StockPage() {
  return (
    <div>
      <EnTetePage titre="Stock" sousTitre="Suivez vos consommables et vos seuils d'alerte." />
      <EtatVide message="La gestion du stock détaillée arrive bientôt. Vos consommables déclarés à l'installation apparaîtront ici." />
    </div>
  );
}
