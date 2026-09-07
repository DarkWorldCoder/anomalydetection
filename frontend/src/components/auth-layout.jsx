import { Brand } from "@/components/brand";
import { Card, CardContent } from "@/components/ui/card";

export function AuthLayout({ children, title, description }) {
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
          <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-slate-950 via-slate-950/85 to-transparent p-10 pt-32 text-white">
            <h2 className="text-3xl font-semibold tracking-tight">{title}</h2>
            <p className="mt-3 max-w-sm text-sm leading-6 text-slate-300">
              {description}
            </p>
          </div>
        </section>
      </Card>
    </main>
  );
}
