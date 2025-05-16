"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";

type ListItem = {
  name: string;
  mainUrl: string;
  imageUrl: string;
  [key: string]: string | number;
};

type ListResponse = {
  title: string;
  criteria: string;
  attributes: Array<{ key: string; name: string }>;
  items: ListItem[];
};

export default function Home() {
  const [categoria, setCategoria] = useState("");
  const [response, setResponse] = useState<ListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState("");

  const fetchData = async (prompt: string) => {
    setLoading(true);
    setErro("");
    try {
      const res = await fetch("https://backend-fastapi-qf8f.onrender.com/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });

      const data = await res.json();

      let raw = data.response;
      raw = raw.trim().replace(/^```json/, "").replace(/```$/, "").trim();

      const parsedData: ListResponse = JSON.parse(raw);
      console.log(parsedData);
      setResponse(parsedData);
    } catch (e) {
      setErro("❌ Ocorreu um erro ao buscar os dados. Tente novamente.");
      setResponse(null);
      console.error("Erro:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleBuscar = () => {
    if (categoria.trim() !== "") {
      fetchData(categoria);
    } else {
      setErro("Digite uma categoria válida para buscar.");
      setResponse(null);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleBuscar();
    }
  };

  return (
    <div className="min-h-screen p-8 flex flex-col gap-6">
      <h1 className="text-2xl font-bold">Listas Top 10</h1>

      <div className="flex gap-4 items-center">
        <input
          type="text"
          value={categoria}
          onChange={(e) => setCategoria(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Digite um tema para a lista"
          className="px-4 py-2 border rounded-md w-64"
        />
        <button
          onClick={handleBuscar}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md"
        >
          Buscar
        </button>
      </div>

      <AnimatePresence>
        {erro && (
          <motion.p
            key="erro"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="text-red-600 bg-red-100 p-3 rounded w-fit"
          >
            {erro}
          </motion.p>
        )}

        {loading && (
          <motion.p
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="text-gray-700 italic"
          >
            🔄 Gerando lista...
          </motion.p>
        )}

        {!loading && !response && !erro && (
          <motion.p
            key="aguardando"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="text-gray-500 italic"
          >
            Aguardando a sua busca...
          </motion.p>
        )}

        {!loading && response && (
          <motion.div
            key="lista"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="overflow-auto"
          >
            <h2 className="text-xl font-semibold mb-2">{response.title}</h2>
            <p className="text-sm text-gray-600 mb-4">Critério: {response.criteria}</p>
            <table className="min-w-full border border-gray-300 text-sm text-left mt-4">
              <thead className="bg-gray-100 font-semibold">
                <tr>
                  <th className="p-2 border-b">Imagem</th>
                  <th className="p-2 border-b">Nome</th>
                  {response.attributes.map((attr) => (
                    <th key={attr.key} className="p-2 border-b">
                      {attr.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {response.items.map((item, index) => (
                  <tr key={index} className="border-t">
                    <td className="p-2">
                      {item.imageUrl && <Image 
                        src={item.imageUrl} 
                        alt={item.name} 
                        width={100} 
                        height={100} 
                        style={{ objectFit: 'cover' }}
                      />}
                    </td>
                    <td className="p-2">
                      <a href={item.mainUrl} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                        {item.name}
                      </a>
                    </td>
                    {response.attributes.map((attr) => (
                      <td key={attr.key} className="p-2">
                        {typeof item[attr.key] === 'object' 
                          ? JSON.stringify(item[attr.key]) 
                          : item[attr.key]}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
