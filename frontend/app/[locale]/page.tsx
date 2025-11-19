import { redirect } from 'next/navigation'

export default function HomePage({ params }: { params: { locale: string } }) {
  // Redirect to playbook by default
  redirect(`/${params.locale}/playbook`)
}
