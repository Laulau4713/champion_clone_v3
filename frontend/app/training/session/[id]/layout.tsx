export default function SessionLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // No header/footer for immersive training experience
  return <>{children}</>;
}
