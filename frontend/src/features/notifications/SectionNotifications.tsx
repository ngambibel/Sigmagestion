import { useState } from "react";
import { Button } from "../../components/ui/Button";
import { usePush } from "./usePush";

export function SectionNotifications() {
  const { supporte, permission, abonne, enCours, activer, desactiver, envoyerTest } = usePush();
  const [message, setMessage] = useState<string | null>(null);

  if (!supporte) {
    return (
      <section className="rounded-2xl bg-papier-surface p-5 shadow-sm">
        <h2 className="mb-2 text-lg">Notifications</h2>
        <p className="text-encre-douce">
          Votre navigateur ne prend pas en charge les notifications push. Sur mobile, installez
          l'application (Ajouter à l'écran d'accueil) puis réessayez.
        </p>
      </section>
    );
  }

  return (
    <section className="mb-6 rounded-2xl bg-papier-surface p-5 shadow-sm">
      <h2 className="mb-2 text-lg">Notifications</h2>
      <p className="mb-4 text-encre-douce">
        Activez les notifications pour être prévenu <strong>avant</strong> une rupture de stock et
        recevoir votre chiffre d'affaires pendant vos horaires — même quand l'application est fermée.
      </p>

      {permission === "denied" ? (
        <p className="rounded-lg bg-magenta-clair p-3 text-sm text-magenta">
          Les notifications sont bloquées dans votre navigateur. Autorisez-les dans les réglages du
          site pour les réactiver.
        </p>
      ) : abonne ? (
        <div className="flex flex-wrap items-center gap-3">
          <span className="rounded-lg bg-valide-clair px-2 py-1 text-sm text-valide">Activées</span>
          <Button
            variante="valide"
            onClick={async () => {
              const r = await envoyerTest();
              setMessage(
                r.envoyees > 0
                  ? "Notification de test envoyée. Elle devrait apparaître dans un instant."
                  : "Aucun appareil abonné.",
              );
            }}
          >
            Envoyer une notification de test
          </Button>
          <Button variante="secondaire" onClick={desactiver} disabled={enCours}>
            Désactiver
          </Button>
        </div>
      ) : (
        <Button onClick={activer} disabled={enCours}>
          {enCours ? "Activation…" : "Activer les notifications"}
        </Button>
      )}

      {message && <p className="mt-3 text-sm text-encre-douce">{message}</p>}
    </section>
  );
}
