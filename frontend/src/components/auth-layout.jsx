import { Brand } from "@/components/brand";
import { Card, CardContent } from "@/components/ui/card";

export function AuthLayout({ children }) {
  return (
    <main className="min-h-svh bg-muted p-4 sm:p-8">
      <Card className="mx-auto grid min-h-[calc(100svh-2rem)] max-w-5xl overflow-hidden py-0 sm:min-h-[calc(100svh-4rem)] lg:grid-cols-2">
        <CardContent className="flex items-center justify-center p-6 sm:p-10">
          <div className="flex w-full max-w-sm flex-col gap-8">
            <Brand />
            {children}
          </div>
        </CardContent>
        <section
          className="relative hidden min-h-[36rem] overflow-hidden bg-slate-950 lg:block"
          aria-label="Protected API network illustration"
        >
          <img
            src="/assets/anomaly-network-login.png"
            alt="Protected API network with an anomalous request highlighted"
            className="absolute inset-0 size-full object-cover"
          />
        </section>
      </Card>
    </main>
  );
}
