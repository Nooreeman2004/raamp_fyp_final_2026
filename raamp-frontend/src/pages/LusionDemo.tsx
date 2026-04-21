import LusionInspiredShowcase from "@/components/LusionInspiredShowcase";
import Layout from "@/components/Layout";

const LusionDemo = () => {
    return (
        <Layout
            showBreadcrumbs
            breadcrumbItems={[
                { label: "Home", href: "/" },
                { label: "Interactive Demo" },
            ]}
        >
            <div className="min-h-screen bg-background">
                <LusionInspiredShowcase />
            </div>
        </Layout>
    );
};

export default LusionDemo;
