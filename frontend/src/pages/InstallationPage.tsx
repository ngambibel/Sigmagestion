import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { OnboardingWizard } from "../features/onboarding/OnboardingWizard";
import { useSecretariats } from "../features/secretariats/useSecretariats";

export default function InstallationPage() {
  const { secretariat, isLoading } = useSecretariats();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-encre-pale">
        Chargement…
      </div>
    );
  }

  return (
    <OnboardingWizard
      secretariatInitial={secretariat}
      onTermine={async () => {
        await queryClient.invalidateQueries({ queryKey: ["secretariats"] });
        navigate("/");
      }}
    />
  );
}
